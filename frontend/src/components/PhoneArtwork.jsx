const phoneImages = import.meta.glob('/src/assets/phones/*', {
  eager: true,
  query: '?url',
  import: 'default',
})

const imageByFilename = Object.fromEntries(
  Object.entries(phoneImages).map(([path, url]) => [path.split('/').pop(), url]),
)

function findImage(imagePath) {
  if (!imagePath) return null
  return imageByFilename[imagePath.split('/').pop()] || null
}

export default function PhoneArtwork({ imagePath, modelName, size = 'medium' }) {
  const source = findImage(imagePath)

  return (
    <div className={`phone-art phone-art--${size}`} aria-label={`${modelName} image`}>
      {source ? (
        <img src={source} alt={modelName} />
      ) : (
        <div className="phone-placeholder" aria-hidden="true">
          <span className="phone-placeholder__speaker" />
          <span className="phone-placeholder__camera" />
          <span className="phone-placeholder__screen">
            <span>{modelName?.slice(0, 1) || 'P'}</span>
          </span>
        </div>
      )}
    </div>
  )
}
