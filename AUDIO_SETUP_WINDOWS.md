# Configuración de Audio para Windows

## Audio está habilitado ✓

Nova usa **sounddevice** para capturar audio del micrófono en Windows. Esta librería es superior a PyAudio porque:

- ✅ No requiere compilación
- ✅ Usa WASAPI (Windows Audio Session API) - la API moderna de Windows
- ✅ Mejor latencia y confiabilidad
- ✅ Mejor soporte para múltiples dispositivos de audio

## Verificar que audio está funcionando

```powershell
# Confirmar que sounddevice está instalado
python -c "import sounddevice; print('✓ sounddevice instalado')"

# Ver dispositivos de audio disponibles
python -c "import sounddevice as sd; print(sd.query_devices())"
```

## Si necesitas PyAudio en lugar de sounddevice

Si por alguna razón necesitas usar PyAudio, debes instalar Visual C++ Build Tools primero:

### Opción 1: Instalar Visual C++ Build Tools (Recomendado para desarrollo)

1. Descargar desde: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Ejecutar el instalador
3. Seleccionar "Desktop development with C++"
4. Instalar
5. Luego instalar PyAudio:
   ```powershell
   pip install PyAudio
   ```

### Opción 2: Descargar wheel precompilado (Más rápido)

Para Python 3.14, buscar en:
- https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

Descargar el archivo `.whl` correspondiente a tu versión de Python e instalar:
```powershell
pip install C:\ruta\al\archivo.whl
```

## Solucionar problemas comunes

### Error: "No se escucha el micrófono"

1. Verificar que el micrófono esté habilitado en Windows:
   - Configuración → Privacidad → Micrófono
   - Asegúrate que las aplicaciones puedan acceder al micrófono

2. Verificar que el micrófono correcto esté seleccionado:
   ```powershell
   python -c "import sounddevice as sd; print(sd.query_devices())"
   ```

3. Probar grabación de audio:
   ```python
   import sounddevice as sd
   import numpy as np
   
   # Grabar 3 segundos
   audio = sd.rec(int(3 * 16000), samplerate=16000, channels=1)
   sd.wait()
   print(f"Grabado: {audio.shape}")
   ```

### Error: "ModuleNotFoundError: No module named 'sounddevice'"

```powershell
pip install sounddevice numpy
```

## Configuración avanzada

Puedes configurar el dispositivo de audio en el `.env`:

```env
# Seleccionar dispositivo de entrada por ID (ver con query_devices())
SOUNDDEVICE_INPUT_DEVICE=0

# Seleccionar dispositivo de salida
SOUNDDEVICE_OUTPUT_DEVICE=0
```

## Más información

- [sounddevice documentation](https://python-sounddevice.readthedocs.io/)
- [Solucionar problemas de audio en Windows](https://support.microsoft.com/es-es/help/4027883/windows-10-fix-sound-problems)
