<script lang="ts">
	import { ChevronLeft, ChevronRight, Calendar } from "lucide-svelte";

	// value au format "YYYY-MM-DDTHH:mm" (compatible datetime-local)
	let { value = $bindable(""), id = "" }: { value: string; id?: string } = $props();

	const MONTHS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"];
	const WEEKDAYS = ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"];

	const pad = (n: number) => String(n).padStart(2, "0");
	const toKey = (y: number, m: number, d: number) => `${y}-${pad(m + 1)}-${pad(d)}`;

	let isOpen = $state(false);
	let viewYear = $state(new Date().getFullYear());
	let viewMonth = $state(new Date().getMonth());

	let datePart = $derived(value ? value.slice(0, 10) : "");
	let timePart = $derived(value && value.length >= 16 ? value.slice(11, 16) : "08:00");

	$effect(() => {
		if (datePart) {
			const [y, m] = datePart.split("-").map(Number);
			viewYear = y;
			viewMonth = m - 1;
		}
	});

	let label = $derived.by(() => {
		if (!datePart) return "Choisir une date";
		const [y, m, d] = datePart.split("-").map(Number);
		const text = new Date(y, m - 1, d).toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
		return `${text} à ${timePart}`;
	});

	let cells = $derived.by(() => {
		const first = new Date(viewYear, viewMonth, 1);
		const offset = (first.getDay() + 6) % 7; // semaine commençant le lundi
		const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
		const out: (number | null)[] = Array(offset).fill(null);
		for (let d = 1; d <= daysInMonth; d++) out.push(d);
		return out;
	});

	const todayKey = (() => {
		const t = new Date();
		return toKey(t.getFullYear(), t.getMonth(), t.getDate());
	})();

	function shiftMonth(delta: number) {
		const d = new Date(viewYear, viewMonth + delta, 1);
		viewYear = d.getFullYear();
		viewMonth = d.getMonth();
	}

	function pickDay(day: number) {
		value = `${toKey(viewYear, viewMonth, day)}T${timePart}`;
	}

	function setTime(e: Event) {
		const t = (e.currentTarget as HTMLInputElement).value || "08:00";
		value = `${datePart || todayKey}T${t}`;
	}
</script>

<div class="relative">
	<button
		{id}
		type="button"
		onclick={() => (isOpen = !isOpen)}
		class="w-full flex items-center gap-2 rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-left text-zinc-100 hover:border-zinc-600 focus:border-cyan-500 focus:outline-none cursor-pointer"
	>
		<Calendar class="w-3.5 h-3.5 text-cyan-400 shrink-0" />
		<span class="truncate capitalize-first">{label}</span>
	</button>

	{#if isOpen}
		<div class="mt-2 rounded-lg border border-app-border bg-app-card p-3 space-y-3">
			<div class="flex items-center justify-between">
				<button type="button" onclick={() => shiftMonth(-1)} class="p-1 rounded-md hover:bg-white/[0.06] text-zinc-300 cursor-pointer" aria-label="Mois précédent">
					<ChevronLeft class="w-4 h-4" />
				</button>
				<span class="text-xs font-semibold text-white">{MONTHS[viewMonth]} {viewYear}</span>
				<button type="button" onclick={() => shiftMonth(1)} class="p-1 rounded-md hover:bg-white/[0.06] text-zinc-300 cursor-pointer" aria-label="Mois suivant">
					<ChevronRight class="w-4 h-4" />
				</button>
			</div>

			<div class="grid grid-cols-7 gap-1 text-center">
				{#each WEEKDAYS as wd}
					<span class="text-[10px] font-medium text-zinc-500 py-1">{wd}</span>
				{/each}
				{#each cells as day}
					{#if day === null}
						<span></span>
					{:else}
						{@const key = toKey(viewYear, viewMonth, day)}
						<button
							type="button"
							onclick={() => pickDay(day)}
							class="aspect-square rounded-md text-xs transition-colors cursor-pointer {key === datePart ? 'bg-cyan-600 text-white font-semibold' : key === todayKey ? 'border border-cyan-500/60 text-cyan-300 hover:bg-white/[0.06]' : 'text-zinc-200 hover:bg-white/[0.06]'}"
						>
							{day}
						</button>
					{/if}
				{/each}
			</div>

			<div class="flex items-center justify-between gap-2 pt-2 border-t border-app-border">
				<label class="flex items-center gap-2 text-xs text-zinc-400">
					Heure
					<input
						type="time"
						value={timePart}
						oninput={setTime}
						class="rounded-lg border border-app-border bg-app-surface px-2 py-1 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none"
					/>
				</label>
				<button type="button" onclick={() => (isOpen = false)} class="px-3 py-1 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold cursor-pointer">
					OK
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.capitalize-first::first-letter {
		text-transform: uppercase;
	}
</style>
