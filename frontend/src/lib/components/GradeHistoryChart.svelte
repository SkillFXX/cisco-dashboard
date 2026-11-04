<script lang="ts">
	import Card from "./Card.svelte";
	import { TrendingUp, TrendingDown, Minus } from "lucide-svelte";

	type Point = { day: string; moyenne: number | null; rang: number | null; total_promo: number | null };

	let { data = [] }: { data: Point[] } = $props();

	const W = 600;
	const H = 190;
	const PAD = { left: 44, right: 14, top: 14, bottom: 30 };

	let metric = $state<"moyenne" | "rang">("moyenne");
	let hoverIndex = $state<number | null>(null);

	let points = $derived(data.filter((d) => d[metric] !== null && d[metric] !== undefined));
	let isRank = $derived(metric === "rang");

	let layout = $derived.by(() => {
		if (points.length === 0) return null;
		const values = points.map((p) => p[metric] as number);
		let lo: number, hi: number;
		if (isRank) {
			lo = 1;
			hi = Math.max(...values, Math.max(...points.map((p) => p.total_promo ?? 0)) || 0, 3);
			// marge visuelle : ne pas forcer toute la promo si la plage observée est étroite
			hi = Math.min(hi, Math.max(Math.max(...values) * 2, Math.max(...values) + 5));
		} else {
			lo = Math.max(0, Math.floor(Math.min(...values) - 1));
			hi = Math.min(20, Math.ceil(Math.max(...values) + 1));
			if (hi - lo < 4) hi = Math.min(20, lo + 4);
		}
		const t0 = new Date(points[0].day).getTime();
		const t1 = new Date(points[points.length - 1].day).getTime();
		const span = Math.max(t1 - t0, 1);
		const innerW = W - PAD.left - PAD.right;
		const innerH = H - PAD.top - PAD.bottom;
		const x = (day: string) => PAD.left + (points.length === 1 ? innerW / 2 : ((new Date(day).getTime() - t0) / span) * innerW);
		// Moyenne : valeur haute en haut. Rang : rang 1 (meilleur) en haut.
		const y = (v: number) => PAD.top + (isRank ? (v - lo) / (hi - lo) : 1 - (v - lo) / (hi - lo)) * innerH;
		const coords = points.map((p) => ({ x: x(p.day), y: y(p[metric] as number), v: p[metric] as number, day: p.day, total: p.total_promo }));
		const path = coords.map((c, i) => `${i === 0 ? "M" : "L"}${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(" ");
		const ticks = [lo, lo + (hi - lo) / 2, hi].map((v) => ({ v: Math.round(v * 10) / 10, y: y(v) }));
		return { coords, path, ticks, t0, t1 };
	});

	let current = $derived(points.length ? (points[points.length - 1][metric] as number) : null);
	let first = $derived(points.length ? (points[0][metric] as number) : null);
	// Pour le rang, une baisse du nombre est une amélioration
	let delta = $derived(current !== null && first !== null ? current - first : 0);
	let improved = $derived(isRank ? delta < 0 : delta > 0);
	let shown = $derived(hoverIndex !== null && layout ? layout.coords[hoverIndex] : null);

	function formatDay(day: string) {
		return new Date(day).toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
	}

	function onMove(e: PointerEvent) {
		if (!layout) return;
		const rect = (e.currentTarget as SVGElement).getBoundingClientRect();
		const px = ((e.clientX - rect.left) / rect.width) * W;
		let best = 0;
		let bestDist = Infinity;
		layout.coords.forEach((c, i) => {
			const d = Math.abs(c.x - px);
			if (d < bestDist) {
				bestDist = d;
				best = i;
			}
		});
		hoverIndex = best;
	}
</script>

<Card class="space-y-3">
	<div class="flex flex-wrap items-start justify-between gap-3">
		<div>
			<h2 class="text-sm font-semibold text-white">Évolution</h2>
			<p class="text-xs text-zinc-400 mt-0.5">Un point par jour de connexion.</p>
		</div>
		<div class="flex p-0.5 bg-app-surface rounded-lg border border-app-border">
			{#each [["moyenne", "Moyenne"], ["rang", "Rang"]] as [id, label]}
				<button
					onclick={() => { metric = id as "moyenne" | "rang"; hoverIndex = null; }}
					class="px-3 py-1.5 text-xs font-semibold rounded-md cursor-pointer transition-all {metric === id ? 'bg-white/[0.1] text-white' : 'text-zinc-400 hover:text-zinc-200'}"
				>{label}</button>
			{/each}
		</div>
	</div>

	{#if !layout}
		<div class="py-10 text-center text-xs text-zinc-500 border border-dashed border-app-border rounded-lg">
			Pas encore de données de {metric === "rang" ? "rang" : "moyenne"}.
		</div>
	{:else}
		<div class="flex items-end gap-3">
			<div class="text-2xl font-bold text-white leading-none">
				{shown ? shown.v : current}{#if isRank}<span class="text-sm text-zinc-400 font-medium">{(shown?.total ?? points[points.length - 1].total_promo) ? ` / ${shown?.total ?? points[points.length - 1].total_promo}` : ""}</span>{:else}<span class="text-sm text-zinc-400 font-medium"> /20</span>{/if}
			</div>
			<div class="text-xs text-zinc-500 pb-0.5">{shown ? formatDay(shown.day) : "Dernier relevé"}</div>
			{#if points.length > 1 && !shown}
				<div class="ml-auto flex items-center gap-1 text-xs font-semibold pb-0.5 {delta === 0 ? 'text-zinc-400' : improved ? 'text-emerald-400' : 'text-rose-400'}">
					{#if delta === 0}<Minus class="w-3.5 h-3.5" />{:else if improved}<TrendingUp class="w-3.5 h-3.5" />{:else}<TrendingDown class="w-3.5 h-3.5" />{/if}
					{delta > 0 ? "+" : ""}{Math.round(delta * 100) / 100} depuis le {formatDay(points[0].day)}
				</div>
			{/if}
		</div>

		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<svg
			viewBox="0 0 {W} {H}"
			class="w-full h-auto touch-pan-y select-none"
			role="img"
			aria-label="Courbe d'évolution de la {metric === 'rang' ? 'position dans la promo' : 'moyenne générale'}"
			onpointermove={onMove}
			onpointerleave={() => (hoverIndex = null)}
		>
			{#each layout.ticks as t}
				<line x1={PAD.left} x2={W - PAD.right} y1={t.y} y2={t.y} stroke="currentColor" class="text-white/[0.06]" />
				<text x={PAD.left - 8} y={t.y + 5} text-anchor="end" class="fill-zinc-500" font-size="15">{t.v}</text>
			{/each}

			<path d={layout.path} fill="none" stroke="rgb(34 211 238)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
			{#each layout.coords as c, i}
				<circle cx={c.x} cy={c.y} r={hoverIndex === i ? 5 : layout.coords.length > 40 ? 0 : 3} fill="rgb(34 211 238)" stroke="#0A0A10" stroke-width="1.5" />
			{/each}
			{#if shown}
				<line x1={shown.x} x2={shown.x} y1={PAD.top} y2={H - PAD.bottom} stroke="rgb(34 211 238)" stroke-opacity="0.35" stroke-dasharray="3 3" />
			{/if}

			<text x={PAD.left} y={H - 8} class="fill-zinc-500" font-size="15">{formatDay(points[0].day)}</text>
			{#if points.length > 1}
				<text x={W - PAD.right} y={H - 8} text-anchor="end" class="fill-zinc-500" font-size="15">{formatDay(points[points.length - 1].day)}</text>
			{/if}
		</svg>

		{#if points.length < 2}
			<p class="text-[11px] text-zinc-500">La courbe se dessinera au fil de vos prochaines connexions.</p>
		{/if}
	{/if}
</Card>
