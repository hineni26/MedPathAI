import { useCallback, useState } from 'react'

export default function useGeolocation() {
  const [position, setPosition] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const requestLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setError('Location is not supported in this browser')
      return Promise.resolve(null)
    }

    setLoading(true)
    setError(null)

    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const next = {
            lat: pos.coords.latitude,
            lon: pos.coords.longitude,
          }
          setPosition(next)
          setLoading(false)
          resolve(next)
        },
        (err) => {
          setError(err.message || 'Could not get your location')
          setLoading(false)
          resolve(null)
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
      )
    })
  }, [])

  return { position, error, loading, requestLocation }
}
