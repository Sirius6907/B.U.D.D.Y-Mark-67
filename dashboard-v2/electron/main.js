// ── B.U.D.D.Y MARK LXVII — Electron Shell ─────────────────────────────
const { app, BrowserWindow, screen, ipcMain } = require("electron");
const path = require("path");

const isDev = !app.isPackaged;

/** @type {BrowserWindow | null} */
let mainWindow = null;

function createWindow() {
  const { width, height, x, y } = screen.getPrimaryDisplay().workArea;
  const targetWidth = Math.max(1024, Math.floor(width * 0.8));
  const targetHeight = Math.max(640, Math.floor(height * 0.8));
  const windowX = x + Math.floor((width - targetWidth) / 2);
  const windowY = y + Math.floor((height - targetHeight) / 2);

  mainWindow = new BrowserWindow({
    width: targetWidth,
    height: targetHeight,
    x: windowX,
    y: windowY,
    minWidth: 1024,
    minHeight: 640,
    frame: false,
    transparent: false,
    backgroundColor: "#03090f",
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.setMenu(null);

  const url = isDev
    ? "http://localhost:3000"
    : `file://${path.join(__dirname, "../out/index.html")}`;

  mainWindow.loadURL(url);

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
    mainWindow.focus();
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

app.whenReady().then(createWindow);

ipcMain.handle("buddy-dashboard:get-ws-url", () => {
  return process.env.BUDDY_DASHBOARD_WS_URL || "ws://127.0.0.1:8765";
});

ipcMain.on("buddy-dashboard:close-window", () => {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.close();
  } else {
    app.quit();
  }
});

app.on("window-all-closed", () => {
  app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
