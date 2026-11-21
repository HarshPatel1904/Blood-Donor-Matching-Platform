import { createContext, useContext, useState, useCallback } from "react";
import { CheckCircle2, AlertCircle, Info } from "lucide-react";

const NotificationContext = createContext(null);

export function NotificationProvider({ children }) {
  const [notifications, setNotifications] = useState([]);

  const removeNotification = useCallback((id) => {
    setNotifications((prev) => prev.filter((item) => item.id !== id));
  }, []);

  const showNotification = useCallback((type, message) => {
    const id = Math.random().toString(36).substring(2, 9);
    setNotifications((prev) => [...prev, { id, type, message }]);

    // Auto-dismiss after 4 seconds
    setTimeout(() => {
      removeNotification(id);
    }, 4000);
  }, [removeNotification]);

  const notifySuccess = useCallback((msg) => showNotification("success", msg), [showNotification]);
  const notifyError = useCallback((msg) => showNotification("danger", msg), [showNotification]);
  const notifyInfo = useCallback((msg) => showNotification("info", msg), [showNotification]);

  return (
    <NotificationContext.Provider value={{ notifySuccess, notifyError, notifyInfo }}>
      {children}
      <div className="toast-container-fixed">
        {notifications.map((item) => {
          const bgClass =
            item.type === "success"
              ? "alert-success border-success"
              : item.type === "danger"
              ? "alert-danger border-danger"
              : "alert-info border-info";

          const IconComponent =
            item.type === "success"
              ? CheckCircle2
              : item.type === "danger"
              ? AlertCircle
              : Info;

          return (
            <div
              key={item.id}
              className={`alert ${bgClass} shadow-sm d-flex align-items-center justify-content-between p-3 mb-2`}
              role="alert"
            >
              <div className="d-flex align-items-center gap-2">
                <IconComponent size={20} className="flex-shrink-0" />
                <span className="small fw-medium">{item.message}</span>
              </div>
              <button
                type="button"
                className="btn-close btn-close-sm ms-2"
                aria-label="Close"
                onClick={() => removeNotification(item.id)}
              />
            </div>
          );
        })}
      </div>
    </NotificationContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useNotification() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error("useNotification must be used within a NotificationProvider");
  }
  return context;
}