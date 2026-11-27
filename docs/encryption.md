# Cifrado de aplicaciÃ³n

La versiÃ³n inicial usa JSON sobre HTTPS. La identidad y las claves JWT son locales y no se usan para cifrar mensajes. JWT firma, pero no oculta los claims.

Si una estaciÃ³n exige cifrado adicional, se diseÃ±arÃ¡ un codec independiente del router, servicios y JWT, con versiÃ³n explÃ­cita y claves separadas por propÃ³sito y estaciÃ³n. Propuesta para revisiÃ³n: AEAD con AES-GCM, nonce Ãºnico por clave, identificador de clave, versiÃ³n, metadatos autenticados y lÃ­mites contra repeticiÃ³n. Definir provisiÃ³n, rotaciÃ³n, vectores de prueba y negociaciÃ³n antes de activarlo. Las versiones no aceptadas deben rechazarse explÃ­citamente. La protecciÃ³n TLS sigue siendo obligatoria.
