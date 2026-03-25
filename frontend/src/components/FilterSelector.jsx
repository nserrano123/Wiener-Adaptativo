import React, { useState } from 'react';
import axios from 'axios';
import './FilterSelector.css';

const FILTER_OPTIONS = [
  { value: 'wiener_adaptive', label: 'Wiener Adaptativo' },
  { value: 'proposal_median', label: 'Mediana Propuesto' },
  { value: 'adaptive_median', label: 'Mediana Adaptativo' },
];

export default function FilterSelector({ imageId, onFilterApplied, onError, onLoading }) {
  const [filterType, setFilterType] = useState('wiener_adaptive');
  const [m, setM] = useState(3);
  const [n, setN] = useState(3);
  const [smax, setSmax] = useState(7);
  const [loading, setLoading] = useState(false);

  function validate() {
    if (filterType === 'wiener_adaptive') {
      if (!Number.isInteger(m) || m < 1) return 'M debe ser un entero >= 1';
      if (!Number.isInteger(n) || n < 1) return 'N debe ser un entero >= 1';
    }
    if (filterType === 'adaptive_median') {
      if (!Number.isInteger(smax) || smax < 3) return 'Smax debe ser un entero >= 3';
    }
    return null;
  }

  function buildParams() {
    if (filterType === 'wiener_adaptive') return { m, n };
    if (filterType === 'adaptive_median') return { smax };
    return {};
  }

  async function handleApply() {
    const validationError = validate();
    if (validationError) {
      onError(validationError);
      return;
    }

    setLoading(true);
    if (onLoading) onLoading(true);
    try {
      const res = await axios.post(
        '/api/filter',
        { image_id: imageId, filter_type: filterType, params: buildParams() },
        { timeout: 120000 }
      );
      const filterLabel = FILTER_OPTIONS.find((o) => o.value === filterType)?.label || filterType;
      onFilterApplied(res.data, filterLabel);
    } catch (err) {
      let msg = 'Error al aplicar el filtro. Intente de nuevo.';
      if (err.code === 'ECONNABORTED') {
        msg = 'La solicitud tardó demasiado. Intente de nuevo más tarde.';
      } else if (!err.response) {
        msg = 'No se pudo conectar con el servidor. Verifique su conexión a internet.';
      } else if (err.response?.data?.error) {
        msg = err.response.data.error;
      }
      onError(msg);
    } finally {
      setLoading(false);
      if (onLoading) onLoading(false);
    }
  }

  const disabled = !imageId || loading;

  return (
    <div className="filter-selector">
      <h2>Seleccionar Filtro</h2>

      <fieldset className="filter-options" disabled={disabled}>
        <legend className="sr-only">Tipo de filtro</legend>
        {FILTER_OPTIONS.map((opt) => (
          <label key={opt.value} className="filter-radio">
            <input
              type="radio"
              name="filterType"
              value={opt.value}
              checked={filterType === opt.value}
              onChange={() => setFilterType(opt.value)}
            />
            {opt.label}
          </label>
        ))}
      </fieldset>

      {filterType === 'wiener_adaptive' && (
        <div className="filter-params">
          <label>
            M (filas vecindad)
            <input
              type="number"
              min="1"
              value={m}
              onChange={(e) => setM(parseInt(e.target.value, 10) || 0)}
              disabled={disabled}
            />
          </label>
          <label>
            N (columnas vecindad)
            <input
              type="number"
              min="1"
              value={n}
              onChange={(e) => setN(parseInt(e.target.value, 10) || 0)}
              disabled={disabled}
            />
          </label>
        </div>
      )}

      {filterType === 'adaptive_median' && (
        <div className="filter-params">
          <label>
            Smax (tamaño máximo ventana)
            <input
              type="number"
              min="3"
              value={smax}
              onChange={(e) => setSmax(parseInt(e.target.value, 10) || 0)}
              disabled={disabled}
            />
          </label>
        </div>
      )}

      <button
        className="apply-btn"
        onClick={handleApply}
        disabled={disabled}
        aria-busy={loading}
      >
        {loading ? 'Procesando…' : 'Aplicar Filtro'}
      </button>

      {!imageId && (
        <p className="filter-hint">Suba una imagen primero para aplicar filtros.</p>
      )}
    </div>
  );
}
