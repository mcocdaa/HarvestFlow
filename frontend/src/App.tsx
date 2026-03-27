import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { MainLayout } from './layouts';
import Dashboard from './pages/Dashboard';
import Sessions from './pages/Sessions';
import Review from './pages/Review';
import Export from './pages/Export';
import Plugins from './pages/Plugins';

const App: React.FC = () => {
  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <MainLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/sessions" element={<Sessions />} />
          <Route path="/review" element={<Review />} />
          <Route path="/export" element={<Export />} />
          <Route path="/plugins" element={<Plugins />} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  );
};

export default App;
