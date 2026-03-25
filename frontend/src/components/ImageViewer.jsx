import React, { useState, useRef, useCallback } from 'react';
import './ImageViewer.css';

const VIEW_LABELS = ['Axial', 'Coronal', 'Sagital'];
const VIEW_KEYS = ['axial', 'coronal', 'sagital'];

function ZoomablePanel({ src, alt, zoom, offset, onZoomChange, onPanChange }) {
  const containerRef = useRef(null);
  const dragging = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });

  const handleWheel = useCallback((e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.15 : 0.15;
    onZoomChange((prev) => Math.max(1, Math.min(prev + delta, 8)));
  }, [onZoomChange]);

  const handleMouseDown = useCallback((e) => {
    if (zoom <= 1) return;
    dragging.current = true;
    lastPos.current = { x: e.clientX, y: e.clientY };
    e.preventDefault();
  }, [zoom]);

  const handleMouseMove = useCallback((e) => {
    if (!dragging.current) return;
    const dx = e.clientX - lastPos.current.x;
    const dy = e.clientY - lastPos.current.y;
    lastPos.current = { x: e.clientX, y: e.clientY };
    onPanChange((prev) => ({ x: prev.x + dx, y: prev.y + dy }));
  }, [onPanChange]);

  const handleMouseUp = useCallback(() => {
    dragging.current = false;
  }, []);

  return (
    <div
      ref={containerRef}
      className="panel-content zoomable"
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <img
        src={src}
        alt={alt}
        draggable={false}
        style={{
          transform: `scale(${zoom}) translate(${offset.x / zoom}px, ${offset.y / zoom}px)`,
          cursor: zoom > 1 ? 'grab' : 'default',
        }}
      />
    </div>
  );
}

export default function ImageViewer({ originalViews, filteredViews, filterLabel, loading }) {
  const [zooms, setZooms] = useState({ axial: 1, coronal: 1, sagital: 1 });
  const [offsets, setOffsets] = useState({
    axial: { x: 0, y: 0 },
    coronal: { x: 0, y: 0 },
    sagital: { x: 0, y: 0 },
  });

  if (!originalViews) return null;

  const makeZoomHandler = (key) => (fn) => {
    setZooms((prev) => {
      const newVal = fn(prev[key]);
      // Reset offset when zooming back to 1
      if (newVal <= 1) {
        setOffsets((p) => ({ ...p, [key]: { x: 0, y: 0 } }));
      }
      return { ...prev, [key]: newVal };
    });
  };

  const makePanHandler = (key) => (fn) => {
    setOffsets((prev) => ({ ...prev, [key]: fn(prev[key]) }));
  };

  const resetZoom = (key) => {
    setZooms((prev) => ({ ...prev, [key]: 1 }));
    setOffsets((prev) => ({ ...prev, [key]: { x: 0, y: 0 } }));
  };

  return (
    <div className="image-viewer">
      {VIEW_KEYS.map((key, i) => (
        <div key={key} className="viewer-column">
          <div className="column-header">
            <h3 className="column-title">{VIEW_LABELS[i]}</h3>
            {zooms[key] > 1 && (
              <button className="reset-zoom-btn" onClick={() => resetZoom(key)}>
                Reset zoom ({zooms[key].toFixed(1)}x)
              </button>
            )}
          </div>
          <div className="viewer-row">
            <div className="viewer-panel">
              <h4 className="panel-title">Original</h4>
              <ZoomablePanel
                src={`data:image/png;base64,${originalViews[key]}`}
                alt={`Original ${VIEW_LABELS[i]}`}
                zoom={zooms[key]}
                offset={offsets[key]}
                onZoomChange={makeZoomHandler(key)}
                onPanChange={makePanHandler(key)}
              />
            </div>
            <div className="viewer-panel">
              <h4 className="panel-title">
                Filtrada{filterLabel ? ` — ${filterLabel}` : ''}
              </h4>
              {loading ? (
                <div className="panel-content">
                  <div className="viewer-loading" role="status">
                    <span className="spinner" aria-hidden="true" />
                    Procesando…
                  </div>
                </div>
              ) : filteredViews ? (
                <ZoomablePanel
                  src={`data:image/png;base64,${filteredViews[key]}`}
                  alt={`Filtrada ${VIEW_LABELS[i]}`}
                  zoom={zooms[key]}
                  offset={offsets[key]}
                  onZoomChange={makeZoomHandler(key)}
                  onPanChange={makePanHandler(key)}
                />
              ) : (
                <div className="panel-content">
                  <p className="viewer-placeholder">Aplique un filtro</p>
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
