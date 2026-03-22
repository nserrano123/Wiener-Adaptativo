import React from 'react';
import './ImageViewer.css';

export default function ImageViewer({ originalUrl, filteredUrl, filterLabel, loading }) {
  if (!originalUrl) return null;

  return (
    <div className="image-viewer">
      <div className="viewer-panel">
        <h3 className="panel-title">Original</h3>
        <div className="panel-content">
          <img src={originalUrl} alt="Imagen original" />
        </div>
      </div>

      <div className="viewer-panel">
        <h3 className="panel-title">
          Filtrada{filterLabel ? ` — ${filterLabel}` : ''}
        </h3>
        <div className="panel-content">
          {loading && (
            <div className="viewer-loading" role="status">
              <span className="spinner" aria-hidden="true" />
              Procesando…
            </div>
          )}
          {!loading && filteredUrl && (
            <img src={filteredUrl} alt={`Imagen filtrada${filterLabel ? ` con ${filterLabel}` : ''}`} />
          )}
          {!loading && !filteredUrl && (
            <p className="viewer-placeholder">Seleccione y aplique un filtro para ver el resultado.</p>
          )}
        </div>
      </div>
    </div>
  );
}
