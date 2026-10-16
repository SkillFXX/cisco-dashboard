<script lang="ts">
	import { onMount } from "svelte";
	import { api } from "$lib/api";
	import { Calendar as CalendarIcon, MapPin, RefreshCw, ChevronLeft, ChevronRight } from "lucide-svelte";
	import Card from "../Card.svelte";

	let timetableData = $state<any>(null);
	let isLoading = $state(true);
	let error = $state("");
	let selectedDayIndex = $state<number | "ALL">("ALL");
	let weekOffset = $state<number>(0);

	async function loadTimetable(forceRefresh = false) {
		isLoading = true;
		error = "";
		try {
			timetableData = await api.getTimetableWeek(forceRefresh);
		} catch (err: any) {
			error = err.message || "Erreur de chargement de l'emploi du temps";
		} finally {
			isLoading = false;
		}
	}

	onMount(() => {
		loadTimetable();
	});

	function getMonday(d: Date): Date {
		const date = new Date(d);
		const day = date.getDay();
		const diff = date.getDate() - day + (day === 0 ? -6 : 1);
		date.setDate(diff);
		date.setHours(0, 0, 0, 0);
		return date;
	}

	let activeMonday = $derived(() => {
		const now = new Date();
		const monday = getMonday(now);
		monday.setDate(monday.getDate() + weekOffset * 7);
		return monday;
	});

	let selectedWeekDays = $derived(() => {
		const days = [];
		const mon = activeMonday();
		const dayNames = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"];
		for (let i = 0; i < 5; i++) {
			const d = new Date(mon);
			d.setDate(mon.getDate() + i);
			const dayNum = d.getDate();
			const monthNum = d.getMonth() + 1;
			const isoDate = d.toISOString().split("T")[0];
			days.push({
				index: i,
				name: dayNames[i],
				formatted: `${dayNum} / ${monthNum}`,
				isoDate,
				fullLabel: `${dayNames[i]} ${dayNum}/${monthNum}`
			});
		}
		return days;
	});

	function eventsForDate(isoDate: string) {
		if (!timetableData?.all_events) return [];
		return timetableData.all_events.filter((e: any) => e.date === isoDate);
	}
</script>

<div class="space-y-6">
	<!-- En-tete avec selecteur de semaine -->
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-app-border">
		<div>
			<h1 class="text-xl font-bold text-white tracking-tight flex items-center gap-2">
				<CalendarIcon class="w-5 h-5 text-cyan-400" />
				<span>Emploi du temps ADE Campus</span>
			</h1>
			<p class="text-xs text-zinc-400 mt-0.5">
				Flux officiel synchronisé avec détection en direct des salles, cours et enseignants.
			</p>
		</div>

		<div class="flex items-center gap-2">
			<!-- Selecteur de semaine -->
			<div class="flex items-center bg-app-card border border-app-border rounded-lg p-1 text-xs">
				<button
					onclick={() => (weekOffset -= 1)}
					class="p-1.5 rounded-md text-zinc-400 hover:text-white hover:bg-white/[0.04] transition-colors cursor-pointer"
					title="Semaine précédente"
				>
					<ChevronLeft class="w-4 h-4" />
				</button>
				<button
					onclick={() => (weekOffset = 0)}
					class="px-2.5 py-1 rounded-md text-xs font-semibold cursor-pointer transition-colors {weekOffset === 0 ? 'text-white font-bold bg-white/[0.08]' : 'text-zinc-300 hover:text-white'}"
				>
					{weekOffset === 0 ? "Cette semaine" : `Semaine ${weekOffset > 0 ? '+' : ''}${weekOffset}`}
				</button>
				<button
					onclick={() => (weekOffset += 1)}
					class="p-1.5 rounded-md text-zinc-400 hover:text-white hover:bg-white/[0.04] transition-colors cursor-pointer"
					title="Semaine suivante"
				>
					<ChevronRight class="w-4 h-4" />
				</button>
			</div>

			<button
				onclick={() => loadTimetable(true)}
				disabled={isLoading}
				class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-app-card hover:bg-white/[0.04] border border-app-border text-xs font-medium text-zinc-300 hover:text-white transition-all cursor-pointer"
			>
				<RefreshCw class="w-3.5 h-3.5 {isLoading ? 'animate-spin text-cyan-400' : ''}" />
				<span>Actualiser</span>
			</button>
		</div>
	</div>

	<!-- Barre de selection jour / semaine complete -->
	<div class="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none border-b border-app-border">
		<button
			onclick={() => (selectedDayIndex = "ALL")}
			class="px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all cursor-pointer {selectedDayIndex === 'ALL'
				? 'bg-white/[0.08] text-white shadow-xs'
				: 'text-zinc-400 hover:text-white hover:bg-white/[0.03]'}"
		>
			Semaine complète
		</button>
		{#each selectedWeekDays() as day}
			{@const count = eventsForDate(day.isoDate).length}
			<button
				onclick={() => (selectedDayIndex = day.index)}
				class="flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all cursor-pointer {selectedDayIndex === day.index
					? 'bg-white/[0.08] text-white font-semibold shadow-xs'
					: 'text-zinc-400 hover:text-white hover:bg-white/[0.03]'}"
			>
				<span>{day.name} ({day.formatted})</span>
				{#if count > 0}
					<span class="text-[10px] px-2 py-0.2 rounded-full bg-zinc-800 text-zinc-200 font-semibold">
						{count}
					</span>
				{/if}
			</button>
		{/each}
	</div>

	{#if isLoading && !timetableData}
		<div class="flex flex-col items-center justify-center p-16 text-zinc-400">
			<RefreshCw class="w-7 h-7 animate-spin text-cyan-400 mb-3" />
			<p class="text-xs">Chargement instantané de l'emploi du temps...</p>
		</div>
	{:else if error}
		<div class="p-4 rounded-lg bg-red-600/20 text-red-300 text-xs font-medium">
			{error}
		</div>
	{:else if timetableData}
		{#if selectedDayIndex === "ALL"}
			<!-- Vue 5 colonnes semaine complete -->
			<div class="grid grid-cols-1 md:grid-cols-5 gap-4">
				{#each selectedWeekDays() as day}
					{@const dayEvents = eventsForDate(day.isoDate)}
					<Card class="p-4 space-y-3">
						<div class="flex items-center justify-between pb-2 border-b border-app-border">
							<div>
								<span class="font-bold text-xs text-zinc-200">{day.name}</span>
								<span class="block text-[10px] text-zinc-500">{day.formatted}</span>
							</div>
							<span class="text-[10px] px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300 font-medium">
								{dayEvents.length} cours
							</span>
						</div>

						<div class="space-y-2.5">
							{#if dayEvents.length === 0}
								<div class="py-8 text-center text-zinc-600 text-xs">
									Aucun cours
								</div>
							{:else}
								{#each dayEvents as evt}
									<div class="p-3 rounded-lg border text-xs space-y-1.5 transition-all {evt.is_current
										? 'border-cyan-500 bg-white/[0.06] text-white shadow-xs'
										: 'border-app-border bg-app-surface hover:border-zinc-700'}">
										<div class="flex items-center justify-between">
											<span class="font-semibold text-[11px] text-zinc-200">{evt.start_time} - {evt.end_time}</span>
											<span class="px-2 py-0.5 rounded-full text-[9px] font-bold {evt.type === 'TP'
												? 'bg-cyan-600 text-white'
												: evt.type === 'TD'
												? 'bg-blue-600 text-white'
												: evt.type === 'CM'
												? 'bg-purple-600 text-white'
												: 'bg-rose-600 text-white'}">
												{evt.type}
											</span>
										</div>

										<div class="font-semibold text-zinc-100 line-clamp-2" title={evt.title}>
											{evt.title}
										</div>

										<div class="pt-1.5 border-t border-app-border flex items-center justify-between text-[11px] text-zinc-400">
											<div class="flex items-center gap-1">
												<MapPin class="w-3 h-3 text-cyan-400 shrink-0" />
												<span class="font-medium text-zinc-300 truncate">{evt.location}</span>
											</div>
											{#if evt.is_current}
												<span class="text-[9px] font-bold text-cyan-400">En direct</span>
											{/if}
										</div>
									</div>
								{/each}
							{/if}
						</div>
					</Card>
				{/each}
			</div>
		{:else}
			<!-- Vue detaillee d'un seul jour -->
			{@const activeDay = selectedWeekDays()[selectedDayIndex]}
			{@const dayEvents = eventsForDate(activeDay.isoDate)}
			<div class="max-w-3xl space-y-4">
				<div class="flex items-center justify-between">
					<h2 class="text-sm font-bold text-white">
						Programme détaillé du {activeDay.fullLabel}
					</h2>
					<span class="text-xs text-zinc-400 bg-app-card border border-app-border px-2.5 py-1 rounded-full">
						{dayEvents.length} cours
					</span>
				</div>

				{#if dayEvents.length === 0}
					<Card class="p-10 text-center text-zinc-500 text-xs">
						Aucun cours programmé pour ce jour.
					</Card>
				{:else}
					<div class="space-y-3">
						{#each dayEvents as evt}
							<Card class="p-4 hover:border-zinc-700">
								<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
									<div class="space-y-1">
										<div class="flex items-center gap-2 flex-wrap">
											<span class="font-bold text-sm text-cyan-400">{evt.start_time} - {evt.end_time}</span>
											<span class="text-xs text-zinc-500">({evt.duration_minutes} min)</span>
											<span class="px-2.5 py-0.5 rounded-full text-xs font-semibold {evt.type === 'TP'
												? 'bg-cyan-600 text-white'
												: evt.type === 'TD'
												? 'bg-blue-600 text-white'
												: evt.type === 'CM'
												? 'bg-purple-600 text-white'
												: 'bg-rose-600 text-white'}">
												{evt.type === 'TP' ? 'Travaux Pratiques (TP)' : evt.type === 'TD' ? 'Travaux Dirigés (TD)' : evt.type === 'CM' ? 'Cours Magistral (CM)' : 'Contrôle (DS)'}
											</span>
											{#if evt.is_current}
												<span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-cyan-600 text-white">
													En cours actuellement
												</span>
											{/if}
										</div>

										<h3 class="text-sm font-bold text-white mt-1">
											{evt.title}
										</h3>
									</div>

									<div class="text-left sm:text-right shrink-0 space-y-1 text-xs">
										<div class="flex items-center sm:justify-end gap-1.5 font-semibold text-zinc-200">
											<MapPin class="w-3.5 h-3.5 text-cyan-400" />
											<span>{evt.location}</span>
										</div>
										{#if evt.teacher}
											<div class="text-zinc-400 text-[11px]">
												{evt.teacher}
											</div>
										{/if}
									</div>
								</div>
							</Card>
						{/each}
					</div>
				{/if}
			</div>
		{/if}
	{/if}
</div>
