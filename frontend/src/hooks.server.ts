import type { Handle } from '@sveltejs/kit';

const SECURITY_HEADERS: Record<string, string> = {
	'X-Content-Type-Options': 'nosniff',
	'X-Frame-Options': 'DENY',
	'Referrer-Policy': 'strict-origin-when-cross-origin',
	'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
};

function withSecurityHeaders(response: Response): Response {
	for (const [name, value] of Object.entries(SECURITY_HEADERS)) {
		response.headers.set(name, value);
	}
	return response;
}

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
		headers.delete('connection');

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

			const upstream = await fetch(targetUrl, fetchOptions);
			// fetch() décompresse le corps : retirer les en-têtes devenus faux
			const responseHeaders = new Headers(upstream.headers);
			responseHeaders.delete('content-encoding');
			responseHeaders.delete('content-length');
			return withSecurityHeaders(
				new Response(upstream.body, {
					status: upstream.status,
					statusText: upstream.statusText,
					headers: responseHeaders
				})
			);
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

	return withSecurityHeaders(await resolve(event));
};

