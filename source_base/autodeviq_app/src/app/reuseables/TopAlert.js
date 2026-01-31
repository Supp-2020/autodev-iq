import { Snackbar, Alert } from "@mui/material";

export default function TopAlert({ open, onClose, typeOfPopup, message }) {
  return (
    <Snackbar
      open={open}
      onClose={onClose}
      anchorOrigin={{ vertical: "top", horizontal: "center" }}
      autoHideDuration={6000}
    >
      <Alert
        onClose={onClose}
        severity={typeOfPopup}
        variant="filled"
        sx={{ width: "100%" }}
      >
        {message}
      </Alert>
    </Snackbar>
  );
}
