'use client';

import Image from 'next/image';
import { useState } from 'react';
import { Box, Button, TextField, Typography, Link, Paper, Dialog, DialogTitle, DialogContent, DialogActions, InputAdornment, IconButton } from '@mui/material';
import { Visibility, VisibilityOff } from "@mui/icons-material";

export default function RegisterPage() {
    const [form, setForm] = useState({
        firstName: '',
        lastName: '',
        email: '',
        password: '',
        confirmPassword: '',
      });

    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [dialogOpen, setDialogOpen] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (
        !form.firstName.trim() ||
        !form.lastName.trim() ||
        !form.email.trim() ||
        !form.password.trim() ||
        !form.confirmPassword.trim()
      ) {
        setError('Please fill in all the fields.');
        return;
      }
  
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
  
    try {
        const res = await fetch('http://localhost:8000/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            firstName: form.firstName,
            lastName: form.lastName,
            email: form.email,
            password: form.password,
          }),
        });
  
        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.detail || 'Registration failed.');
        }
        setDialogOpen(true);
      } catch (err) {
        console.error(err);
        setError(err.message);
      }
    };

    const handleDialogClose = () => {
        setDialogOpen(false);
        window.location.href = '/login';
      };

      const togglePasswordVisibility = () => {
        setShowPassword((prev) => !prev);
      };
    
      const toggleConfirmPasswordVisibility = () => {
        setShowConfirmPassword((prev) => !prev);
      };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#1976d2] p-4">
      <div className="mb-6">
        <Image src="/logo.png" alt="Auto DevIQ Logo" width={120} height={120} />
      </div>

      <Paper elevation={6} className="w-full max-w-md p-8 rounded-2xl">
        <Typography variant="h5" component="h2" gutterBottom align="center">
          Register
        </Typography>

        <Box component="form" onSubmit={handleSubmit} noValidate>
          <TextField
            fullWidth
            label="First Name"
            name="firstName"
            value={form.firstName}
            onChange={handleChange}
            margin="normal"
            required
          />

          <TextField
            fullWidth
            label="Last Name"
            name="lastName"
            value={form.lastName}
            onChange={handleChange}
            margin="normal"
            required
          />

          <TextField
            fullWidth
            label="Email Address"
            name="email"
            type="email"
            value={form.email}
            onChange={handleChange}
            margin="normal"
            required
          />

          <TextField
            fullWidth
            label="Password"
            name="password"
            type={showPassword ? "text" : "password"}
            value={form.password}
            onChange={handleChange}
            margin="normal"
            required
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={togglePasswordVisibility} edge="end">
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <TextField
            fullWidth
            label="Confirm Password"
            name="confirmPassword"
            type={showConfirmPassword ? "text" : "password"}
            value={form.confirmPassword}
            onChange={handleChange}
            margin="normal"
            required
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={toggleConfirmPasswordVisibility} edge="end">
                    {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

            {error && (
                <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                    {error}
                </Typography>
            )}

            {success && (
            <Typography variant="body2" color="primary" sx={{ mt: 1 }}>
                {success}
            </Typography>
            )}

          <Button
            type="submit"
            variant="contained"
            fullWidth
            sx={{
                mt: 3,
                bgcolor: '#1976d2',
                '&:hover': {
                  bgcolor: '#1976d1',
                },
              }}
          >
            Register
          </Button>
        </Box>

        <Typography variant="body2" align="center" sx={{ mt: 2 }}>
          Already have an account?{' '}
          <Link href="/login" underline="hover" color="primary">
            Login
          </Link>
        </Typography>

        <Dialog open={dialogOpen} onClose={handleDialogClose}>
        <DialogTitle>Success</DialogTitle>
        <DialogContent>
          <Typography>Registration successful! Click OK to proceed to login.</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose} autoFocus>
            OK
          </Button>
        </DialogActions>
      </Dialog>
      </Paper>

    </div>
  );
}
