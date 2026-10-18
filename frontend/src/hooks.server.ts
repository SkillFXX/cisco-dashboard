import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
	const pathname = event.url.pathname;

	// Proxy automatique vers le backend FastAPI (port 8000)
	if (
		pathname.startsWith('/api/') ||
		pathname.startsWith('/docs') ||
		pathname.startsWith('/openapi.json')
	) {
		const backendUrl = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';
		const targetUrl = `${backendUrl}${pathname}${event.url.search}`;

		const headers = new Headers(event.request.headers);
		headers.delete('host');

		try {
			const fetchOptions: RequestInit = {
				method: event.request.method,
				headers,
				body:
					event.request.method !== 'GET' && event.request.method !== 'HEAD'
						? event.request.body
						: undefined,
				// @ts-ignore
				duplex: 'half'
			};

			return await fetch(targetUrl, fetchOptions);
		} catch (err) {
			console.error(`Erreur proxy backend vers ${targetUrl}:`, err);
			return new Response(
				JSON.stringify({ detail: 'Backend FastAPI indisponible ou en cours de redémarrage.' }),
				{
					status: 502,
					headers: { 'Content-Type': 'application/json' }
				}
			);
		}
	}

	return resolve(event);
};
