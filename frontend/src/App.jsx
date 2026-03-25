import React, { useState } from 'react';
import axios from 'axios';
import ImageUploader from './components/ImageUploader';
import FilterSelector from './components/FilterSelector';
import ImageViewer from './components/ImageViewer';
import './App.css';

function App() {
  const [imageId, setImageId] = useState(null);
  const [originalViews, setOriginalViews] = useState(null);
  const [filteredViews, setFilteredViews] = useState(null);
  const [filterLabel, setFilterLabel] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleUpload(id, previewUrl) {
    setImageId(id);
    setFilteredViews(null);
    setFilterLabel(null);
    setError('');
    try {
      const res = await axios.get(`/api/images/${id}/views`);
      setOriginalViews(res.data);
    } catch {
      setOriginalViews(null);
      setError('Error al cargar las vistas de la imagen.');
    }
  }

  function handleFilterApplied(views, label) {
    setFilteredViews(views);
    setFilterLabel(label);
    setError('');
  }

  function handleError(msg) {
    setError(msg);
  }

  return (
    <div className="app">
      <h1>Filtros de Imágenes Médicas</h1>
      <div className="app-controls">
        <ImageUploader onUpload={handleUpload} />
        <FilterSelector
          imageId={imageId}
          onFilterApplied={handleFilterApplied}
          onError={handleError}
          onLoading={setLoading}
        />
      </div>
      {error && <div className="app-error" role="alert">{error}</div>}
      <ImageViewer
        originalViews={originalViews}
        filteredViews={filteredViews}
        filterLabel={filterLabel}
        loading={loading}
      />
    </div>
  );
}

export default App;
