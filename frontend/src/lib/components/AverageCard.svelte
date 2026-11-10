<script lang="ts">
	import { formatGrade } from "$lib/utils";
	import Card from "./Card.svelte";
	import Sparkline from "./Sparkline.svelte";

	let {
		stats,
		series = [],
		onclick
	}: {
		stats: any;
		series?: number[];
		onclick?: () => void;
	} = $props();

	let clickable = $derived(!!onclick);
</script>

<Card
	class="p-4 space-y-2 relative overflow-hidden {clickable ? 'cursor-pointer hover:border-subtle' : ''}"
	role={clickable ? "button" : undefined}
	tabindex={clickable ? 0 : undefined}
	aria-label={clickable ? "Voir l'évolution de la moyenne" : undefined}
	onclick={() => onclick?.()}
	onkeydown={(e: KeyboardEvent) => e.key === "Enter" && onclick?.()}
>
	{#if series.length > 1}
		<div class="absolute top-3 right-3 bottom-12 w-[52%] pointer-events-none">
			<Sparkline values={series} color="#0891b2" />
		</div>
	{/if}
	<span class="relative text-[11px] font-semibold uppercase tracking-wider text-muted">Moyenne générale</span>
	<div class="relative flex items-baseline gap-1.5">
		<span class="text-2xl sm:text-3xl font-black text-fg">{formatGrade(stats?.moyenne_generale)}</span>
		<span class="text-xs text-subtle font-semibold">/ 20</span>
	</div>
	<div class="pt-1.5 border-t border-app-border flex items-center justify-between text-[11px] text-muted">
		<span>Min <strong class="text-fg font-medium">{formatGrade(stats?.min_promo)}</strong></span>
		<span>Moy <strong class="text-fg font-medium">{formatGrade(stats?.moy_promo)}</strong></span>
		<span>Max <strong class="text-fg font-medium">{formatGrade(stats?.max_promo)}</strong></span>
	</div>
</Card>
