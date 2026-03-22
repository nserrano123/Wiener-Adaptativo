import React, { useState, useRef } from 'react';
import axios from 'axios';
import './ImageUploader.css';

const ALLOWED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.dcm', '.nii', '.gz'];

function getExtension(filename) {
  const lower = filename.toLowerCase();
  if (lower.endsWith('.nii.gz')) return '.nii';
  const dot = lower.lastIndexOf('.');
  return dot !== -1 ? lower.slice(dot) : '';
}

export default function ImageUploader({ onUpload }) {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const fileRef = useRef(null);

  async function handleUpload() {
    setError('');
    const file = fileRef.current?.files?.[0];
    if (!file) {
      setError('Seleccione un archivo de imagen.');
      return;
    }

    const ext = getExtension(file.name);
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setError(`Formato no soportado (${ext || 'desconocido'}). Use: ${ALLOWED_EXTENSIONS.join(', ')}`);
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    try {
      const res = await axios.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
      });
      const { image_id, preview_url } = res.data;
      setPreviewUrl(preview_url);
      onUpload(image_id, preview_url);
    } catch (err) {
      let msg = 'Error al subir la imagen. Intente de nuevo.';
      if (err.code === 'ECONNABORTED') {
        msg = 'La carga tardó demasiado. Intente de nuevo más tarde.';
      } else if (!err.response) {
        msg = 'No se pudo conectar con el servidor. Verifique su conexión a internet.';
      } else if (err.response?.data?.error) {
        msg = err.response.data.error;
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="image-uploader">
      <h2>Cargar Imagen</h2>
      <div className="upload-area">
        <input
          ref={fileRef}
          type="file"
          accept=".png,.jpg,.jpeg,.dcm,.nii,.nii.gz,.gz"
          aria-label="Seleccionar imagen"
        />
        <button onClick={handleUpload} disabled={loading}>
          {loading ? 'Subiendo…' : 'Subir'}
        </button>
      </div>
      {error && <div className="upload-error" role="alert">{error}</div>}
      {previewUrl && (
        <div className="upload-preview">
          <img src={previewUrl} alt="Vista previa de imagen cargada" />
        </div>
      )}
    </div>
  );
}
