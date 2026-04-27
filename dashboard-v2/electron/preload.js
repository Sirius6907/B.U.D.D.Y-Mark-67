const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("buddyDesktop", {
  getWebSocketUrl: () => ipcRenderer.invoke("buddy-dashboard:get-ws-url"),
  closeWindow: () => ipcRenderer.send("buddy-dashboard:close-window"),
});
