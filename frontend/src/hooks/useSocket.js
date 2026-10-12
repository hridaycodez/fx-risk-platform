import { useEffect, useState, useCallback, useRef } from 'react';
import { io } from 'socket.io-client';

const rawSocketUrl = import.meta.env.VITE_SOCKET_URL;
const SOCKET_URL = rawSocketUrl || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:4000');

/**
 * Custom React hook for Socket.io connection.
 * Uses useState so React re-renders when socket connects/disconnects.
 * Handles JWT auth, connection lifecycle, and event subscriptions.
 *
 * Usage:
 *   const { socket, connected, emit } = useSocket();
 *   useSocketEvent(socket, 'mc_chunk', (data) => { ... });
 */
export function useSocket() {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    const token = localStorage.getItem('fx_token');
    if (!token) return;

    // Avoid creating duplicate connections
    if (socketRef.current) return;

    const s = io(SOCKET_URL, {
      auth: { token },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 2000,
    });

    s.on('connect', () => {
      console.log('🔌 Socket connected:', s.id);
      setConnected(true);
    });

    s.on('disconnect', () => {
      console.log('🔌 Socket disconnected');
      setConnected(false);
    });

    s.on('connect_error', (err) => {
      console.error('Socket connection error:', err.message);
    });

    socketRef.current = s;
    setSocket(s);
    if (s.connected) {
      setConnected(true);
    }

    return () => {
      s.disconnect();
      socketRef.current = null;
      setSocket(null);
      setConnected(false);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const emit = useCallback((event, data) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
    }
  }, []);

  return { socket, connected, emit };
}

/**
 * Subscribe to a socket event — automatically cleans up on unmount.
 */
export function useSocketEvent(socket, event, handler) {
  useEffect(() => {
    if (!socket) return;
    socket.on(event, handler);
    return () => socket.off(event, handler);
  }, [socket, event, handler]);
}
