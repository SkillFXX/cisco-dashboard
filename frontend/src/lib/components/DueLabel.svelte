<script lang="ts">
	let { daysLeft, long = false }: { daysLeft: number; long?: boolean } = $props();
	const unit = $derived(long ? (daysLeft > 1 ? "jours" : "jour") : "j");
</script>

{#if daysLeft < 0}
	<span class="rounded-md px-2 py-0.5 text-[11px] font-semibold bg-rose-600/15 text-rose-400">En retard · {Math.abs(daysLeft)} {long ? (Math.abs(daysLeft) > 1 ? "jours" : "jour") : "j"}</span>
{:else if daysLeft <= 1}
	<span class="rounded-md px-2 py-0.5 text-[11px] font-semibold bg-amber-600/15 text-amber-400">{daysLeft === 0 ? "Aujourd'hui" : "Demain"}</span>
{:else}
	<span class="text-xs font-medium text-fg">Dans {daysLeft} {unit}</span>
{/if}
