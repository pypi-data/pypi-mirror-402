import { Canvas } from './components/Canvas';
import { PropertyPanel } from './components/PropertyPanel';
import { Toolbar } from './components/Toolbar';
import { MessagesPanel } from './components/MessagesPanel';
import './tokens.css';

function App() {
  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <Toolbar />
      <div style={{ display: 'flex', height: '100%', paddingTop: '48px' }}>
        <MessagesPanel />
        <Canvas />
        <PropertyPanel />
      </div>
    </div>
  );
}

export default App;
