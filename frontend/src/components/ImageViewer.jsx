import React from 'react';
import './ImageViewer.css';

const VIEW_LABELS = ['Axial', 'Coronal', 'Sagital'];
const VIEW_KEYS = ['axial', 'coronal', 'sagital'];

export default function ImageViewer({ originalViews, filteredViews, filterLabel, loading }) {
  if (!originalViews) return null;

  return (
    <div className="image-viewer">
      {VIEW_KEYS.map((key, i) => (
        <div key={key} className="viewer-column">
          <h3 className="column-title">{VIEW_LABELS[i]}</h3>
          <div className="viewer-row">
            <div className="viewer-panel">
              <h4 className="panel-title">Original</h4>
              <div className="panel-content">
                <img src={`data:image/png;base64,${originalViews[key]}`} alt={`Original ${VIEW_LABELS[i]}`} />
              </div>
            </div>
            <div className="viewer-panel">
              <h4 className="panel-title">
                Filtrada{filterLabel ? ` — ${filterLabel}` : ''}
              </h4>
              <div className="panel-content">
                {loading && (
                  <div className="viewer-loading" role="status">
                    <span className="spinner" aria-hidden="true" />
                    Procesando…
                  </div>
                )}
                {!loading && filteredViews && (
                  <img src={`data:image/png;base64,${filteredViews[key]}`} alt={`Filtrada ${VIEW_LABELS[i]}`} />
                )}
                {!loading && !filteredViews && (
                  <p className="viewer-placeholder">Aplique un filtro</p>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
