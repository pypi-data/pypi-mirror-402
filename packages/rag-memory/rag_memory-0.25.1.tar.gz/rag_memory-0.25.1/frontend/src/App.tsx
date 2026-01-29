import { useEffect } from 'react';
import { useRagStore } from './rag/store';
import { AppLayout } from './rag/components/layout/AppLayout';

function App() {
  const { connect, loadCollections } = useRagStore();

  useEffect(() => {
    // Initialize WebSocket connection
    connect(async () => null); // No auth for now

    // Load initial data
    loadCollections();
  }, [connect, loadCollections]);

  return <AppLayout />;
}

export default App;
