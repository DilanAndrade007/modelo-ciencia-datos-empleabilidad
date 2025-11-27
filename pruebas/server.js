import express from 'express';
import LinkedInAPI from '@atharvh01/linkedin-jobs-api'; // Importamos lo que sea que exporte

const app = express();
const PORT = 3000;

// Usamos la función exportada directamente como handler
app.get('/api/search', async (req, res, next) => {
  try {
    // Llamamos la función directamente, pasando req y res
    await LinkedInAPI(req, res);
  } catch (err) {
    console.error('❌ Error en la búsqueda:', err);
    next(err);
  }
});

// Ruta de prueba
app.get('/', (req, res) => {
  res.json({
    message: '✅ API de LinkedIn Jobs corriendo',
    ejemplo: '/api/search?keywords=react&location=remote'
  });
});

// Ruta de estado
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    time: new Date().toISOString()
  });
});

// Error 500
app.use((err, req, res, next) => {
  res.status(500).json({
    success: false,
    error: err.message || 'Error interno'
  });
});

// Ruta 404
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    error: 'Ruta no encontrada'
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Servidor activo en http://localhost:${PORT}`);
});
