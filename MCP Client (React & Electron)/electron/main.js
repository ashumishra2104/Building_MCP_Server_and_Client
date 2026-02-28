const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const fs = require('fs');

let mainWindow;
let backendProcess;

// ─── Resolve the project directory ───────────────────────────────────────────
// In dev: the electron/ folder is inside the project
// In production: we read the baked-in project-path.json
const isDev = !app.isPackaged;

let projectDir;
if (isDev) {
    projectDir = path.join(__dirname, '..');
} else {
    // Read the path we baked in at build time
    const pathFile = path.join(__dirname, 'project-path.json');
    projectDir = JSON.parse(fs.readFileSync(pathFile, 'utf8')).projectDir;
}

const backendScript = path.join(projectDir, 'backend.py');
const activateScript = path.join(projectDir, '.venv', 'bin', 'activate');

console.log(`[electron] projectDir: ${projectDir}`);
console.log(`[electron] backendScript: ${backendScript}`);
console.log(`[electron] activate: ${activateScript}`);

// ─── Start FastAPI backend via bash (preserves venv symlinks) ────────────────
function startBackend() {
    if (!fs.existsSync(backendScript)) {
        dialog.showErrorBox('Startup Error', `backend.py not found at:\n${backendScript}`);
        app.quit();
        return;
    }

    let bashCmd;
    if (fs.existsSync(activateScript)) {
        // Proper venv activation — bash handles all symlinks correctly
        bashCmd = `source "${activateScript}" && python "${backendScript}"`;
    } else {
        // Fallback: try system python3 (user may have packages installed globally)
        bashCmd = `python3 "${backendScript}"`;
    }

    console.log(`[electron] Running: bash -l -c "${bashCmd}"`);

    backendProcess = spawn('/bin/bash', ['-l', '-c', bashCmd], {
        cwd: projectDir,
        env: { ...process.env, PYTHONUNBUFFERED: '1' },
        stdio: ['ignore', 'pipe', 'pipe'],
    });

    backendProcess.stdout.on('data', (d) => process.stdout.write('[backend] ' + d));
    backendProcess.stderr.on('data', (d) => process.stderr.write('[backend] ' + d));
    backendProcess.on('exit', (code, signal) => {
        console.log(`[electron] Backend exited code=${code} signal=${signal}`);
    });
}

// ─── Poll until backend is ready ─────────────────────────────────────────────
function waitForBackend(url, retries = 40, interval = 500) {
    return new Promise((resolve, reject) => {
        const attempt = (n) => {
            const req = http.get(url, (res) => {
                res.resume();
                console.log(`[electron] Backend responded ${res.statusCode}`);
                if (res.statusCode < 500) resolve();
                else if (n > 0) setTimeout(() => attempt(n - 1), interval);
                else reject(new Error('Backend returned error status'));
            });
            req.on('error', () => {
                if (n > 0) setTimeout(() => attempt(n - 1), interval);
                else reject(new Error('Backend not reachable after timeout'));
            });
            req.end();
        };
        attempt(retries);
    });
}

// ─── Create main window ───────────────────────────────────────────────────────
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 900,
        height: 700,
        title: 'MCP Chat',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
        },
    });

    mainWindow.loadURL('http://localhost:8000');
    // Uncomment during debugging:
    // mainWindow.webContents.openDevTools();
    mainWindow.on('closed', () => { mainWindow = null; });
}

// ─── App lifecycle ────────────────────────────────────────────────────────────
app.whenReady().then(async () => {
    startBackend();
    try {
        await waitForBackend('http://localhost:8000');
        createWindow();
    } catch (err) {
        dialog.showErrorBox('Startup Error',
            `Failed to start backend:\n\n${err.message}\n\nProject directory:\n${projectDir}\n\nMake sure the .venv exists at:\n${projectDir}/.venv`
        );
        app.quit();
    }
});

app.on('window-all-closed', () => {
    if (backendProcess) backendProcess.kill();
    if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
    if (mainWindow === null) createWindow();
});

app.on('will-quit', () => {
    if (backendProcess) backendProcess.kill();
});
