import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { DetalleOrden } from './paginas/DetalleOrden';
import { ListadoOrdenes } from './paginas/ListadoOrdenes';
import { NuevaOrden } from './paginas/NuevaOrden';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ListadoOrdenes />} />
        <Route path="/ordenes/nueva" element={<NuevaOrden />} />
        <Route path="/ordenes/:id" element={<DetalleOrden />} />
      </Routes>
    </BrowserRouter>
  );
}
