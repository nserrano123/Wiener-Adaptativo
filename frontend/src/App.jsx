import React, { useState } from 'react';
import ImageUploader from './components/ImageUploader';
import FilterSelector from './components/FilterSelector';
import ImageViewer from './components/ImageViewer';
import './App.css';

function App() {
  const [imageId, setImageId] = useState(null);
  const [originalUrl, setOriginalUrl] = useState(null);
  const [filteredUrl, setFilteredUrl] = useState(null);
  const [filterLabel, setFilterLabel] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function handleUpload(id, previewUrl) {
    setImageId(id);
    setOriginalUrl(previewUrl);
    setFilteredUrl(null);
    setFilterLabel(null);
    setError('');
  }

  function handleFilterApplied(url, label) {
    setFilteredUrl(url);
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

      {error && (
        <div className="app-error" role="alert">
          {error}
        </div>
      )}

      <ImageViewer
        originalUrl={originalUrl}
        filteredUrl={filteredUrl}
        filterLabel={filterLabel}
        loading={loading}
      />
    </div>
  );
}

export default App;
