const SIZE = 512

/**
 * Prepara a foto no próprio celular antes do upload: recorta em quadrado e reduz para
 * 512x512. Assim o envio fica leve até no 4G e fotos do iPhone (HEIC) viram JPEG.
 * O servidor ainda regrava a imagem (e remove metadados): isto aqui é só conforto.
 */
export async function preparePhoto(file: File): Promise<Blob> {
  if (file.type && !file.type.startsWith('image/')) {
    throw new Error('Escolha um arquivo de imagem.')
  }

  let bitmap: ImageBitmap
  try {
    // Já aplica a rotação que o celular grava na foto.
    bitmap = await createImageBitmap(file)
  } catch {
    throw new Error('Não consegui abrir essa foto. Tenta outra (JPG ou PNG)?')
  }

  // Recorte quadrado; em foto "em pé", puxa para cima, onde costuma estar o rosto.
  const side = Math.min(bitmap.width, bitmap.height)
  const sx = (bitmap.width - side) / 2
  const sy = bitmap.height > bitmap.width ? (bitmap.height - side) * 0.3 : 0

  const canvas = document.createElement('canvas')
  canvas.width = SIZE
  canvas.height = SIZE
  const context = canvas.getContext('2d')
  if (!context) throw new Error('Seu navegador não conseguiu processar a foto.')
  context.imageSmoothingQuality = 'high'
  context.fillStyle = '#fff' // PNG transparente fica com fundo branco
  context.fillRect(0, 0, SIZE, SIZE)
  context.drawImage(bitmap, sx, sy, side, side, 0, 0, SIZE, SIZE)
  bitmap.close()

  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.9))
  if (!blob) throw new Error('Seu navegador não conseguiu processar a foto.')
  return blob
}
