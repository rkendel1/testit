import React, { useState, useEffect, useRef } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { WebLinksAddon } from 'xterm-addon-web-links';
import 'xterm/css/xterm.css';
import './Terminal.css';

const TerminalComponent = ({ sessionId, apiUrl }) => {
  const terminalRef = useRef(null);
  const [terminal, setTerminal] = useState(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!terminalRef.current) return;

    // Create terminal
    const term = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
      theme: {
        background: '#1e1e1e',
        foreground: '#d4d4d4',
        cursor: '#d4d4d4'
      },
      cols: 100,
      rows: 30
    });

    const fitAddon = new FitAddon();
    const webLinksAddon = new WebLinksAddon();
    
    term.loadAddon(fitAddon);
    term.loadAddon(webLinksAddon);
    
    term.open(terminalRef.current);
    fitAddon.fit();

    setTerminal(term);

    // Handle window resize
    const handleResize = () => {
      fitAddon.fit();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      term.dispose();
    };
  }, []);

  useEffect(() => {
    if (!terminal || !sessionId) return;

    // Connect to WebSocket
    // Construct WebSocket URL based on the API URL
    let wsUrl;
    
    // Parse the API URL to get the hostname and port
    try {
      const apiUrlObj = new URL(apiUrl);
      const wsProtocol = apiUrlObj.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = apiUrlObj.host; // includes port if present
      wsUrl = `${wsProtocol}//${host}/api/terminal/${sessionId}`;
    } catch (e) {
      // Fallback for malformed URLs
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = apiUrl.replace('http://', '').replace('https://', '');
      wsUrl = `${wsProtocol}//${wsHost}/api/terminal/${sessionId}`;
    }

    terminal.writeln('Connecting to container terminal...');
    terminal.writeln(`WebSocket URL: ${wsUrl}\r\n`);

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      terminal.writeln('Connected!\r\n');
      setConnected(true);

      // Send data from terminal to WebSocket
      terminal.onData(data => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(data);
        }
      });
    };

    ws.onmessage = (event) => {
      terminal.write(event.data);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      terminal.writeln(`\r\n${'\x1b[31m'}WebSocket error: Connection failed${'\x1b[0m'}`);
      terminal.writeln('Please ensure the backend is running and accessible.\r\n');
      setConnected(false);
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      terminal.writeln(`\r\n${'\x1b[33m'}Connection closed.${'\x1b[0m'}`);
      if (event.code !== 1000) {
        terminal.writeln(`Close code: ${event.code}, Reason: ${event.reason || 'Unknown'}\r\n`);
      }
      setConnected(false);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [terminal, sessionId, apiUrl]);

  return (
    <div className="terminal-container">
      <div className="terminal-header">
        <span className="terminal-title">Container Terminal</span>
        <span className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? '● Connected' : '○ Disconnected'}
        </span>
      </div>
      <div ref={terminalRef} className="terminal"></div>
    </div>
  );
};

export default TerminalComponent;
