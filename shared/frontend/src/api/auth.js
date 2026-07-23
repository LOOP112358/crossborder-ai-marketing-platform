import request from './request'

export function login(username, password) {
  return request.post('/auth/login', { username, password })
}

export function register(username, password) {
  return request.post('/auth/register', { username, password })
}

export function getMe() {
  return request.get('/auth/me')
}
