<script lang="ts">
	import { onMount } from "svelte";
	import Card from "../Card.svelte";
	import Badge from "../Badge.svelte";
	import Button from "../Button.svelte";
	import { api } from "$lib/api";
	import { CalendarDays, MapPin, User as UserIcon, Clock, Users, RefreshCw } from "lucide-svelte";

	let timetableData = $state<any>(null);
	let isLoading = $state(true);
	let error = $state("");
	let selectedDay = $state<string>("ALL");

	const daysOfWeek = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"];

	// Determine current day of week (0 = Monday in France)
	const currentDayIndex = new Date().getDay(); // 0 is Sunday, 1 is Monday
	const defaultDay = currentDayIndex >= 1 && currentDayIndex <= 5 ? daysOfWeek[currentDayIndex - 1] : "Lundi";

	async function loadTimetable() {
		isLoading = true;
		error = "";
		try {
			timetableData = await api.getTimetableWeek();
			selectedDay = defaultDay;
		} catch (err: any) {
			error = err.message || "Erreur lors de la récupération de l'emploi du temps.";
		} finally {
			isLoading = false;
		}
	}

	onMount(() => {
		loadTimetable();
	});

	let eventsForDay = $derived((day: string) => {
		if (!timetableData?.all_events) return [];
		return timetableData.all_events.filter((e: any) => e.day_name === day);
	});
</script>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
		<div>
			<h1 class="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
				<CalendarDays class="w-6 h-6 text-cyan-400" />
				Emploi du Temps ADE Campus
			</h1>
			<p class="text-sm text-zinc-400 mt-1">
				Synchronisé via votre flux iCal ADE Campus (Université de Montpellier). Détection en direct des cours et salles.
			</p>
		</div>

		<div class="flex items-center gap-3">
			<Button variant="outline" size="sm" onclick={loadTimetable} disabled={isLoading}>
				<RefreshCw class="w-4 h-4 {isLoading ? 'animate-spin' : ''}" />
				<span>Actualiser ADE</span>
			</Button>
		</div>
	</div>

	<!-- Day Selector Bar -->
	<div class="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none border-b border-zinc-800">
		<button
			onclick={() => (selectedDay = "ALL")}
			class="px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer {selectedDay === 'ALL' ? 'bg-cyan-500 text-zinc-950 shadow-md shadow-cyan-500/20' : 'bg-zinc-900 text-zinc-400 hover:text-white hover:bg-zinc-800'}"
		>
			Semaine Complète
		</button>
		{#each daysOfWeek as day}
			<button
				onclick={() => (selectedDay = day)}
				class="px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer {selectedDay === day ? 'bg-cyan-500 text-zinc-950 shadow-md shadow-cyan-500/20' : 'bg-zinc-900 text-zinc-400 hover:text-white hover:bg-zinc-800'}"
			>
				{day}
			</button>
		{/each}
	</div>

	{#if isLoading}
		<div class="flex flex-col items-center justify-center p-12 text-zinc-400">
			<RefreshCw class="w-8 h-8 animate-spin text-cyan-400 mb-3" />
			<p class="text-sm">Lecture et analyse de votre flux iCal ADE Campus...</p>
		</div>
	{:else if error}
		<div class="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
			{error}
		</div>
	{:else if timetableData}
		{#if selectedDay === "ALL"}
			<!-- 5-Day Weekly View -->
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
				{#each daysOfWeek as day}
					{@const dayEvents = eventsForDay(day)}
					<div class="space-y-3">
						<div class="flex items-center justify-between px-1">
							<h3 class="font-bold text-sm text-zinc-200">{day}</h3>
							<span class="text-xs text-zinc-500">{dayEvents.length} cours</span>
						</div>

						<div class="space-y-2.5">
							{#if dayEvents.length === 0}
								<div class="p-4 rounded-xl border border-dashed border-zinc-800/80 bg-zinc-950/20 text-center text-xs text-zinc-500">
									Aucun cours
								</div>
							{:else}
								{#each dayEvents as evt}
									<div class="p-3 rounded-xl border transition-all text-xs {evt.is_current ? 'border-cyan-500 bg-cyan-950/30 ring-1 ring-cyan-500/50' : 'border-zinc-800/80 bg-zinc-900/60 hover:border-zinc-700'}">
										<div class="flex items-center justify-between mb-1.5">
											<span class="font-mono font-semibold text-zinc-200">{evt.start_time} - {evt.end_time}</span>
											{#if evt.type === 'TP'}
												<Badge variant="tp">TP</Badge>
											{:else if evt.type === 'TD'}
												<Badge variant="td">TD</Badge>
											{:else if evt.type === 'CM'}
												<Badge variant="cm">CM</Badge>
											{:else if evt.type === 'DS'}
												<Badge variant="ds">DS</Badge>
											{/if}
										</div>

										<div class="font-bold text-zinc-100 line-clamp-2" title={evt.title}>
											{evt.title}
										</div>

										<div class="mt-2 pt-2 border-t border-zinc-800/60 space-y-1 text-zinc-400">
											<div class="flex items-center gap-1.5">
												<MapPin class="w-3 h-3 text-cyan-400 shrink-0" />
												<span class="truncate font-medium text-zinc-300">{evt.location}</span>
											</div>
											{#if evt.teacher}
												<div class="flex items-center gap-1.5 text-zinc-500">
													<UserIcon class="w-3 h-3 shrink-0" />
													<span class="truncate">{evt.teacher}</span>
												</div>
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
			<!-- Single Day Detailed View -->
			{@const dayEvents = eventsForDay(selectedDay)}
			<div class="max-w-3xl space-y-4">
				<div class="flex items-center justify-between">
					<h2 class="text-lg font-bold text-white">Programme détaillé du {selectedDay}</h2>
					<Badge variant="cisco">{dayEvents.length} cours programmés</Badge>
				</div>

				{#if dayEvents.length === 0}
					<Card class="text-center py-10 text-zinc-500 text-sm">
						Aucun cours prévu le {selectedDay}. Profitez-en pour réviser ou travailler sur votre SAÉ !
					</Card>
				{:else}
					<div class="space-y-3">
						{#each dayEvents as evt}
							<div class="p-4 rounded-xl border transition-all {evt.is_current ? 'border-cyan-500 bg-cyan-950/20 ring-1 ring-cyan-500' : 'border-zinc-800 bg-zinc-900/60 hover:border-zinc-700'}">
								<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
									<div class="space-y-1">
										<div class="flex items-center gap-2 flex-wrap">
											<span class="font-mono font-bold text-sm text-cyan-400">{evt.start_time} - {evt.end_time}</span>
											<span class="text-xs text-zinc-500">({evt.duration_minutes} min)</span>
											{#if evt.type === 'TP'}
												<Badge variant="tp">Travaux Pratiques (TP)</Badge>
											{:else if evt.type === 'TD'}
												<Badge variant="td">Travaux Dirigés (TD)</Badge>
											{:else if evt.type === 'CM'}
												<Badge variant="cm">Cours Magistral (CM)</Badge>
											{:else if evt.type === 'DS'}
												<Badge variant="ds">Contrôle / Évaluation (DS)</Badge>
											{/if}
											{#if evt.is_current}
												<Badge variant="cisco" class="animate-pulse">En cours actuellement</Badge>
											{/if}
										</div>

										<h3 class="text-base font-bold text-white mt-1">
											{evt.title}
										</h3>
									</div>

									<div class="text-left sm:text-right shrink-0 space-y-1">
										<div class="flex items-center sm:justify-end gap-1.5 text-sm font-semibold text-zinc-200">
											<MapPin class="w-4 h-4 text-cyan-400" />
											<span>{evt.location}</span>
										</div>
										{#if evt.teacher}
											<div class="text-xs text-zinc-400">
												{evt.teacher}
											</div>
										{/if}
										{#if evt.group}
											<div class="text-[11px] text-zinc-500">
												{evt.group}
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

