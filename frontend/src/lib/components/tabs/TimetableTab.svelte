<script lang="ts">
	import { onMount } from "svelte";
	import { api } from "$lib/api";
	import {
		CalendarDays,
		MapPin,
		User as UserIcon,
		Clock,
		RefreshCw,
		ChevronLeft,
		ChevronRight
	} from "lucide-svelte";

	let timetableData = $state<any>(null);
	let isLoading = $state(true);
	let error = $state("");
	let selectedDayIndex = $state<number | "ALL">("ALL");
	let weekOffset = $state(0); // 0 = semaine courante, -1 = precedente, +1 = suivante

	// Calcul des jours de la semaine selectionnee (Lundi a Vendredi)
	let selectedWeekDays = $derived(() => {
		const baseNow = new Date();
		const currentWeekday = (baseNow.getDay() + 6) % 7; // 0 = Lundi, ..., 4 = Vendredi
		const monday = new Date(baseNow);
		monday.setDate(baseNow.getDate() - currentWeekday + (weekOffset * 7));

		const names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"];
		return [0, 1, 2, 3, 4].map((i) => {
			const d = new Date(monday);
			d.setDate(monday.getDate() + i);
			return {
				name: names[i],
				index: i,
				isoDate: d.toISOString().slice(0, 10),
				formatted: `${d.getDate()} / ${(d.getMonth() + 1).toString().padStart(2, "0")}`,
				fullLabel: `${names[i]} ${d.getDate()}/${(d.getMonth() + 1).toString().padStart(2, "0")}`
			};
		});
	});

	async function loadTimetable(forceRefresh = false) {
		isLoading = true;
		error = "";
		try {
			timetableData = await api.getTimetableWeek(forceRefresh);
		} catch (err: any) {
			error = err.message || "Erreur lors de la récupération de l'emploi du temps.";
		} finally {
			isLoading = false;
		}
	}

	onMount(() => {
		loadTimetable();
	});

	// Filtrage strict par date ISO reelle de la semaine selectionnee
	let eventsForDate = $derived((isoDate: string) => {
		if (!timetableData?.all_events) return [];
		return timetableData.all_events
			.filter((e: any) => e.date === isoDate)
			.sort((a: any, b: any) => a.start_time.localeCompare(b.start_time));
	});
</script>

<div class="space-y-6">
	<!-- En-tete avec commandes de semaine -->
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
		<div>
			<h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
				<CalendarDays class="w-5 h-5 text-cyan-400" />
				Emploi du temps ADE Campus
			</h1>
			<p class="text-xs text-zinc-400 mt-0.5">
				Flux officiel synchronisé avec détection en direct des salles, cours et enseignants.
			</p>
		</div>

		<div class="flex items-center gap-2">
			<!-- Selecteur de semaine -->
			<div class="flex items-center bg-[#0E121B] border border-[#182030] rounded-xl p-1 text-xs">
				<button
					onclick={() => (weekOffset -= 1)}
					class="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-[#151C2A] transition-colors cursor-pointer"
					title="Semaine précédente"
				>
					<ChevronLeft class="w-4 h-4" />
				</button>
				<button
					onclick={() => (weekOffset = 0)}
					class="px-2.5 py-1 rounded-lg text-xs font-semibold cursor-pointer transition-colors {weekOffset === 0 ? 'text-cyan-400 font-bold' : 'text-zinc-300 hover:text-white'}"
				>
					{weekOffset === 0 ? "Cette semaine" : `Semaine ${weekOffset > 0 ? '+' : ''}${weekOffset}`}
				</button>
				<button
					onclick={() => (weekOffset += 1)}
					class="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-[#151C2A] transition-colors cursor-pointer"
					title="Semaine suivante"
				>
					<ChevronRight class="w-4 h-4" />
				</button>
			</div>

			<button
				onclick={() => loadTimetable(true)}
				disabled={isLoading}
				class="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-[#0E121B] hover:bg-[#151C2A] border border-[#182030] text-xs font-medium text-zinc-300 hover:text-white transition-all cursor-pointer"
			>
				<RefreshCw class="w-3.5 h-3.5 {isLoading ? 'animate-spin text-cyan-400' : ''}" />
				<span>Actualiser</span>
			</button>
		</div>
	</div>

	<!-- Barre de selection jour / semaine complete -->
	<div class="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none border-b border-[#182030]">
		<button
			onclick={() => (selectedDayIndex = "ALL")}
			class="px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer {selectedDayIndex === 'ALL'
				? 'bg-cyan-950/60 text-cyan-400 border border-cyan-800/40'
				: 'text-zinc-400 hover:text-zinc-200 hover:bg-[#0E121B]'}"
		>
			Semaine complète
		</button>
		{#each selectedWeekDays() as day}
			{@const count = eventsForDate(day.isoDate).length}
			<button
				onclick={() => (selectedDayIndex = day.index)}
				class="flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all cursor-pointer {selectedDayIndex === day.index
					? 'bg-cyan-950/60 text-cyan-400 border border-cyan-800/40 font-semibold'
					: 'text-zinc-400 hover:text-zinc-200 hover:bg-[#0E121B]'}"
			>
				<span>{day.name} ({day.formatted})</span>
				{#if count > 0}
					<span class="text-[10px] px-1.5 py-0.2 rounded-full bg-[#151C2A] text-zinc-300 font-mono">
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
		<div class="p-4 rounded-xl bg-red-950/30 border border-red-800/40 text-red-400 text-xs">
			{error}
		</div>
	{:else if timetableData}
		{#if selectedDayIndex === "ALL"}
			<!-- Vue 5 colonnes semaine complete -->
			<div class="grid grid-cols-1 md:grid-cols-5 gap-4">
				{#each selectedWeekDays() as day}
					{@const dayEvents = eventsForDate(day.isoDate)}
					<div class="bg-[#0E121B] border border-[#182030] rounded-2xl p-4 space-y-3">
						<div class="flex items-center justify-between pb-2 border-b border-[#182030]">
							<div>
								<span class="font-bold text-xs text-zinc-200">{day.name}</span>
								<span class="block text-[10px] text-zinc-500 font-mono">{day.formatted}</span>
							</div>
							<span class="text-[10px] px-2 py-0.5 rounded-full bg-[#151C2A] text-zinc-400 font-mono">
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
									<div class="p-3 rounded-xl border text-xs space-y-1.5 transition-all {evt.is_current
										? 'border-cyan-500 bg-[#0E2A38] text-white shadow-sm'
										: 'border-[#182030] bg-[#080A0F] hover:border-zinc-700'}">
										<div class="flex items-center justify-between">
											<span class="font-mono font-semibold text-[11px] text-zinc-200">{evt.start_time} - {evt.end_time}</span>
											<span class="px-1.5 py-0.2 rounded font-mono text-[9px] font-bold {evt.type === 'TP'
												? 'bg-cyan-950/60 text-cyan-400 border border-cyan-800/40'
												: evt.type === 'TD'
												? 'bg-blue-950/60 text-blue-400 border border-blue-800/40'
												: evt.type === 'CM'
												? 'bg-indigo-950/60 text-indigo-400 border border-indigo-800/40'
												: 'bg-rose-950/60 text-rose-400 border border-rose-800/40'}">
												{evt.type}
											</span>
										</div>

										<div class="font-semibold text-zinc-100 line-clamp-2" title={evt.title}>
											{evt.title}
										</div>

										<div class="pt-1.5 border-t border-[#182030] flex items-center justify-between text-[11px] text-zinc-400">
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
					</div>
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
					<span class="text-xs font-mono text-zinc-400 bg-[#0E121B] border border-[#182030] px-2.5 py-1 rounded-xl">
						{dayEvents.length} cours
					</span>
				</div>

				{#if dayEvents.length === 0}
					<div class="bg-[#0E121B] border border-[#182030] rounded-2xl p-10 text-center text-zinc-500 text-xs">
						Aucun cours programmé pour ce jour.
					</div>
				{:else}
					<div class="space-y-3">
						{#each dayEvents as evt}
							<div class="bg-[#0E121B] border border-[#182030] rounded-2xl p-4 transition-all hover:border-zinc-700">
								<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
									<div class="space-y-1">
										<div class="flex items-center gap-2 flex-wrap">
											<span class="font-mono font-bold text-sm text-cyan-400">{evt.start_time} - {evt.end_time}</span>
											<span class="text-xs text-zinc-500">({evt.duration_minutes} min)</span>
											<span class="px-2 py-0.5 rounded font-mono text-xs font-semibold {evt.type === 'TP'
												? 'bg-cyan-950/60 text-cyan-400 border border-cyan-800/40'
												: evt.type === 'TD'
												? 'bg-blue-950/60 text-blue-400 border border-blue-800/40'
												: evt.type === 'CM'
												? 'bg-indigo-950/60 text-indigo-400 border border-indigo-800/40'
												: 'bg-rose-950/60 text-rose-400 border border-rose-800/40'}">
												{evt.type === 'TP' ? 'Travaux Pratiques (TP)' : evt.type === 'TD' ? 'Travaux Dirigés (TD)' : evt.type === 'CM' ? 'Cours Magistral (CM)' : 'Contrôle (DS)'}
											</span>
											{#if evt.is_current}
												<span class="px-2 py-0.5 rounded text-xs font-bold bg-cyan-950 text-cyan-300 border border-cyan-500">
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
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{/if}
	{/if}
</div>
