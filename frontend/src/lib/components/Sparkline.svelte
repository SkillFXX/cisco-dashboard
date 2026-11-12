<script lang="ts">
	import { smoothPath } from "$lib/utils";
	// Mini-courbe décorative : apparaît en fondu (dégradé) et se dessine de gauche à droite.
	let {
		values,
		invert = false,
		color = "#22d3ee"
	}: { values: number[]; invert?: boolean; color?: string } = $props();

	const uid = $props.id();
	const W = 200;
	const H = 80;
	const PAD = 8;

	let geometry = $derived.by(() => {
		const lo = Math.min(...values);
		const hi = Math.max(...values);
		const span = hi - lo || 1;
		const coords = values.map((v, i) => {
			const x = values.length === 1 ? W / 2 : PAD + (i / (values.length - 1)) * (W - 2 * PAD);
			const ratio = (v - lo) / span;
			// Pour le rang (invert), la meilleure valeur (la plus basse) est en haut
			const y = PAD + (invert ? ratio : 1 - ratio) * (H - 2 * PAD);
			return { x, y };
		});
		const line = smoothPath(coords);
		const area = `${line} L${coords[coords.length - 1].x.toFixed(1)},${H} L${coords[0].x.toFixed(1)},${H} Z`;
		return { line, area, last: coords[coords.length - 1] };
	});
</script>

<div class="spark relative w-full h-full">
	<svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" class="w-full h-full overflow-visible" aria-hidden="true">
		<defs>
			<linearGradient id="spark-{uid}" x1="0" y1="0" x2="0" y2="1">
				<stop offset="0%" stop-color={color} stop-opacity="0.32" />
				<stop offset="100%" stop-color={color} stop-opacity="0" />
			</linearGradient>
		</defs>
		<path d={geometry.area} fill="url(#spark-{uid})" />
		<path d={geometry.line} fill="none" stroke={color} stroke-width="2" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke" />
	</svg>
	<span
		class="dot absolute w-2 h-2 -ml-1 -mt-1 rounded-full ring-2 ring-app-card"
		style="left: {(geometry.last.x / W) * 100}%; top: {(geometry.last.y / H) * 100}%; background: {color};"
	></span>
</div>

<style>
	.spark {
		/* Dégradé d'apparition : transparent à gauche, plein à droite */
		-webkit-mask-image: linear-gradient(to right, transparent 0%, #000 60%);
		mask-image: linear-gradient(to right, transparent 0%, #000 60%);
		animation: spark-reveal 1.1s cubic-bezier(0.22, 1, 0.36, 1) 0.1s both;
	}
	.dot {
		animation: dot-in 0.4s ease-out 1s both;
	}
	@keyframes spark-reveal {
		from { clip-path: inset(0 100% 0 0); opacity: 0; }
		to { clip-path: inset(0 0 0 0); opacity: 1; }
	}
	@keyframes dot-in {
		from { transform: scale(0); }
		to { transform: scale(1); }
	}
	@media (prefers-reduced-motion: reduce) {
		.spark, .dot { animation: none; }
	}
</style>
