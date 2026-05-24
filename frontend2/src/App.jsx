import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { PlayerProvider } from './contexts/PlayerContext';
import { DownloadProvider } from './contexts/DownloadContext';
import { ToastProvider } from './components/Toast';
import Layout from './components/Layout';
import Home from './pages/Home';
import Discovery from './pages/Discovery';
import Chatbot from './pages/Chatbot';
import Playlists from './pages/Playlists';
import Downloads from './pages/Downloads';
import AudioEditor from './pages/AudioEditor';
import Feedback from './pages/Feedback';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <PlayerProvider>
          <DownloadProvider>
            <ToastProvider>
              <Routes>
                <Route element={<Layout />}>
                  <Route path="/" element={<Home />} />
                  <Route path="/discover" element={<Discovery />} />
                  <Route path="/chat" element={<Chatbot />} />
                  <Route path="/playlists" element={<Playlists />} />
                  <Route path="/downloads" element={<Downloads />} />
                  <Route path="/editor" element={<AudioEditor />} />
                  <Route path="/feedback" element={<Feedback />} />
                </Route>
              </Routes>
            </ToastProvider>
          </DownloadProvider>
        </PlayerProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
