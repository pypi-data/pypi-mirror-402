from scipy.ndimage import gaussian_filter

def zsurf_gpu(self, z_floor: float = None, v_exag: float = 0.5, sigma: float = 1.0):
    # ... código anterior ...
    
    # Aplicamos un filtro suave para eliminar el bandeado visual
    # sigma=1.0 es un valor muy conservador que quita el ruido sin perder detalle
    Z_smooth = gaussian_filter(self.Z, sigma=sigma)
    
    # Usamos Z_smooth para el gráfico, pero los datos originales siguen en self.Z
    fig = go.Figure(
        data=[go.Surface(z=Z_smooth, x=self.X, y=self.Y, colorscale="earth")]
    )
    
    # ... resto del layout ...