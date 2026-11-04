/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />
import { immutable, assets } from '$app/manifest';
import { version } from '$app/env';

const sw = self as unknown as ServiceWorkerGlobalScope;
const CACHE = `cisco-${version}`;
const ASSETS = [...immutable, ...assets].map((entry) => entry.path);

// Mise en cache de l'application (coquille) : les données de l'API ne sont jamais conservées ici
sw.addEventListener('install', (event) => {
	event.waitUntil(
		caches
			.open(CACHE)
			.then(async (cache) => {
				await cache.addAll(ASSETS);
				// Page d'accueil (sans donnée personnelle) pour l'ouverture hors-ligne
				await cache.add('/').catch(() => {});
			})
			.then(() => sw.skipWaiting())
	);
});

sw.addEventListener('activate', (event) => {
	event.waitUntil(
		caches
			.keys()
			.then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
			.then(() => sw.clients.claim())
	);
});

sw.addEventListener('fetch', (event) => {
	const { request } = event;
	if (request.method !== 'GET') return;

	const url = new URL(request.url);
	if (url.origin !== sw.location.origin || url.pathname.startsWith('/api/')) return;

	event.respondWith(
		(async () => {
			const cache = await caches.open(CACHE);

			// Ressources versionnées : cache d'abord
			if (ASSETS.includes(url.pathname)) {
				const cached = await cache.match(url.pathname);
				if (cached) return cached;
			}

			try {
				return await fetch(request);
			} catch (err) {
				// Hors-ligne : page d'accueil en cache pour les navigations
				if (request.mode === 'navigate') {
					const fallback = await cache.match('/');
					if (fallback) return fallback;
				}
				throw err;
			}
		})()
	);
});
