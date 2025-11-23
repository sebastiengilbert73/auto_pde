import { useState, useEffect } from 'react'
import './App.css'
import { checkHealth, solvePDE } from './api/client'
import PDEForm from './components/PDEForm'
import SolutionVisualizer from './components/SolutionVisualizer'

import ErrorBoundary from './components/ErrorBoundary'

function App() {
  const [status, setStatus] = useState('Checking backend...');
  const [isSolving, setIsSolving] = useState(false);
  const [solution, setSolution] = useState(null);

  useEffect(() => {
    checkHealth()
      .then(data => setStatus(`Backend: ${data.status}`))
      .catch(() => setStatus('Backend: Disconnected'));
  }, []);

  const handleSolve = async (formData) => {
    setIsSolving(true);
    try {
      const result = await solvePDE(formData);
      setSolution(result);
      console.log('Solution:', result);
    } catch (error) {
      console.error('Error solving PDE:', error);
      alert('Failed to solve PDE: ' + error.message);
    } finally {
      setIsSolving(false);
    }
  };

  return (
    <div className="app-container">
      <header>
        <h1>PDE Solver</h1>
        <div className="status-indicator" style={{
          padding: '0.5rem',
          backgroundColor: status.includes('healthy') ? '#dcfce7' : '#fee2e2',
          color: status.includes('healthy') ? '#166534' : '#991b1b',
          borderRadius: '4px',
          fontSize: '0.875rem',
          marginTop: '0.5rem'
        }}>
          {status}
        </div>
      </header>
      <main>
        <p>Welcome to the PDE Solver. Configure your problem below.</p>
        <PDEForm onSubmit={handleSolve} isLoading={isSolving} />

        {solution && (
          <div style={{ marginTop: '2rem', padding: '1rem', background: '#f0f9ff', borderRadius: '8px' }}>
            <h3>Solution Computed!</h3>
            <ErrorBoundary>
              <SolutionVisualizer solution={solution.data} />
            </ErrorBoundary>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
