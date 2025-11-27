addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

const invoices = {} // store invoices in memory

async function handleRequest(request) {
  const url = new URL(request.url)
  const path = url.pathname
  const method = request.method

  if (path === '/status') {
    return new Response(JSON.stringify({ status: 'ok' }), {
      headers: { 'Content-Type': 'application/json' }
    })
  }

  if (path === '/invoices' && method === 'POST') {
    const body = await request.json()
    const id = 'INV-' + Date.now()
    invoices[id] = { ...body, ebmStatus: 'success', id }
    return new Response(JSON.stringify({ id, ebmStatus: 'success' }), {
      headers: { 'Content-Type': 'application/json' }
    })
  }

  if (path.startsWith('/invoices/') && method === 'GET') {
    const id = path.split('/')[2]
    const invoice = invoices[id]
    if (invoice) {
      return new Response(JSON.stringify(invoice), {
        headers: { 'Content-Type': 'application/json' }
      })
    } else {
      return new Response(JSON.stringify({ error: 'Not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' }
      })
    }
  }

  return new Response(JSON.stringify({ error: 'Invalid route' }), {
    status: 400,
    headers: { 'Content-Type': 'application/json' }
  })
  }
