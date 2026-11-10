<script lang="ts">
	import { onMount } from "svelte";
	import { api } from "$lib/api";
	import {
		ChevronLeft,
		ChevronRight,
		RefreshCw
	} from "lucide-svelte";
	import {
		toLocalIsoDate,
		getMondayOfDate,
		getCourseColorStyle
	} from "$lib/utils";
	import Card from "../Card.svelte";
	import Skeleton from "../Skeleton.svelte";
	import CourseDetailModal from "../CourseDetailModal.svelte";

	let { onAddTaskForCourse }: { onAddTaskForCourse?: (course: any) => void } = $props();

	let timetableData = $state<any>(null);
	let isLoading = $state(true);
	let error = $state("");

	// Mode d'affichage : "week" (semaine) ou "month" (mois)
	let viewMode = $state<"week" | "month">("week");

	// Décalage temporel
	let weekOffset = $state<number>(0);
	let monthOffset = $state<number>(0);

	// Modal de détail d'un cours
	let selectedCourse = $state<any>(null);
	let isModalOpen = $state<boolean>(false);

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

	function openCourseDetail(course: any) {
		selectedCourse = course;
		isModalOpen = true;
	}

	function parseTimeToMinutes(timeStr: string): number {
		if (!timeStr) return 0;
		const [h, m] = timeStr.split(":").map((v) => parseInt(v, 10));
		return h * 60 + (m || 0);
	}

	const now = new Date();
	const todayIso = toLocalIsoDate(now);

	// ----------------------------------------------------
	// VUE MOBILE : un seul jour à la fois (week-ends ignorés)
	// ----------------------------------------------------
	function isoToDate(iso: string): Date {
		const [y, m, d] = iso.split("-").map(Number);
		return new Date(y, m - 1, d, 12, 0, 0);
	}

	function nextWorkingDay(from: Date, step: 1 | -1): Date {
		const d = new Date(from);
		do {
			d.setDate(d.getDate() + step);
		} while (d.getDay() === 0 || d.getDay() === 6);
		return d;
	}

	const startDay = now.getDay() === 0 || now.getDay() === 6 ? nextWorkingDay(now, 1) : now;
	let mobileDayIso = $state(toLocalIsoDate(startDay));

	function setMobileDay(d: Date) {
		mobileDayIso = toLocalIsoDate(d);
		const diffDays = Math.round((getMondayOfDate(d, 0).getTime() - getMondayOfDate(now, 0).getTime()) / 86400000);
		weekOffset = Math.round(diffDays / 7);
	}

	function stepMobileDay(step: 1 | -1) {
		setMobileDay(nextWorkingDay(isoToDate(mobileDayIso), step));
	}

	let touchStartX = 0;
	function onDayTouchStart(e: TouchEvent) {
		touchStartX = e.changedTouches[0].clientX;
	}
	function onDayTouchEnd(e: TouchEvent) {
		const dx = e.changedTouches[0].clientX - touchStartX;
		if (Math.abs(dx) > 60) stepMobileDay(dx < 0 ? 1 : -1);
	}

	let mobileDayEvents = $derived(() =>
		(timetableData?.all_events || [])
			.filter((e: any) => e.date === mobileDayIso)
			.sort((a: any, b: any) => a.start_time.localeCompare(b.start_time))
			.map((e: any) => ({ ...e, colorStyle: getCourseColorStyle(e.type) }))
	);

	let mobileDayLabel = $derived(() =>
		isoToDate(mobileDayIso).toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" })
	);

	// ----------------------------------------------------
	// CALCULS DE LA VUE SEMAINE (Même logique robuste que le tableau de bord)
	// ----------------------------------------------------
	let activeMonday = $derived(() => {
		return getMondayOfDate(now, weekOffset);
	});

	let weekDays = $derived(() => {
		const mon = activeMonday();
		const dayNames = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];
		const fullDayNames = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"];
		const days = [];
		const all = timetableData?.all_events || [];

		// Détecter si le samedi comporte des cours dans cette semaine
		const sat = new Date(mon);
		sat.setDate(mon.getDate() + 5);
		const satIso = toLocalIsoDate(sat);
		const hasSaturdayEvents = all.some((e: any) => e.date === satIso);
		const countDays = hasSaturdayEvents ? 6 : 5;

		for (let offset = 0; offset < countDays; offset++) {
			const d = new Date(mon);
			d.setDate(mon.getDate() + offset);
			const isoDate = toLocalIsoDate(d);
			days.push({
				name: dayNames[offset],
				fullName: fullDayNames[offset],
				offset,
				isoDate,
				dayNumber: d.getDate(),
				formattedDate: `${d.getDate()} / ${(d.getMonth() + 1).toString().padStart(2, "0")}`,
				isToday: isoDate === todayIso
			});
		}
		return days;
	});

	// Échelle horaire de 08:00 à 18:30 (total 630 minutes)
	const dayStartMinutes = 8 * 60; // 480
	const dayEndMinutes = 18 * 60 + 30; // 1110
	const totalDayMinutes = dayEndMinutes - dayStartMinutes; // 630

	// Cours positionnés pour la semaine sélectionnée
	let weekEvents = $derived(() => {
		const raw = timetableData?.all_events || [];
		if (!raw || raw.length === 0) return [];

		const days = weekDays();
		if (days.length === 0) return [];

		const startIso = days[0].isoDate;
		const endIso = days[days.length - 1].isoDate;

		return raw
			.filter((e: any) => e.date >= startIso && e.date <= endIso)
			.map((e: any) => {
				const startMins = parseTimeToMinutes(e.start_time);
				const endMins = parseTimeToMinutes(e.end_time);
				const duration = Math.max(endMins - startMins, 45);

				// Index du jour dans la grille (0 = Lundi, 4 = Vendredi, 5 = Samedi)
				const dayIdx = days.findIndex((d) => d.isoDate === e.date);

				const topPercent = Math.min(Math.max(((startMins - dayStartMinutes) / totalDayMinutes) * 100, 0), 91);
				const heightPercent = Math.min(Math.max((duration / totalDayMinutes) * 100, 7), 50);

				// Style unifié identique au tableau de bord
				const colorStyle = getCourseColorStyle(e.type);

				return {
					...e,
					dayIdx,
					topPercent,
					heightPercent,
					colorStyle
				};
			});
	});

	// Indicateur horizontal heure courante (semaine actuelle uniquement)
	let currentTimeIndicator = $derived(() => {
		if (weekOffset !== 0) return null;
		const currentWeekday = (now.getDay() + 6) % 7;
		const days = weekDays();
		if (currentWeekday >= days.length) return null;

		const currentMins = now.getHours() * 60 + now.getMinutes();
		if (currentMins < dayStartMinutes || currentMins > dayEndMinutes) return null;

		const topPercent = ((currentMins - dayStartMinutes) / totalDayMinutes) * 100;
		const hoursStr = now.getHours().toString().padStart(2, "0");
		const minsStr = now.getMinutes().toString().padStart(2, "0");

		return {
			topPercent,
			dayIdx: currentWeekday,
			timeLabel: `${hoursStr}:${minsStr}`
		};
	});

	let weekRangeLabel = $derived(() => {
		const days = weekDays();
		if (days.length === 0) return "";
		const first = days[0];
		const last = days[days.length - 1];
		return `Du ${first.formattedDate} au ${last.formattedDate}`;
	});

	// ----------------------------------------------------
	// CALCULS DE LA VUE MOIS
	// ----------------------------------------------------
	let activeMonthDate = $derived(() => {
		return new Date(now.getFullYear(), now.getMonth() + monthOffset, 1, 12, 0, 0);
	});

	let monthLabel = $derived(() => {
		const d = activeMonthDate();
		const monthNames = [
			"Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
			"Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
		];
		return `${monthNames[d.getMonth()]} ${d.getFullYear()}`;
	});

	let monthMatrix = $derived(() => {
		const target = activeMonthDate();
		const year = target.getFullYear();
		const month = target.getMonth();

		// Premier jour du mois
		const firstDay = new Date(year, month, 1, 12, 0, 0);
		// Jour de la semaine (0 = Lundi, 6 = Dimanche)
		const startDayOfWeek = (firstDay.getDay() + 6) % 7;

		// Nombre de jours dans le mois
		const daysInMonth = new Date(year, month + 1, 0).getDate();
		// Nombre de jours dans le mois précédent
		const daysInPrevMonth = new Date(year, month, 0).getDate();

		const matrix: any[] = [];
		const allEvents = timetableData?.all_events || [];

		// Jours du mois précédent pour combler la première semaine
		for (let i = startDayOfWeek - 1; i >= 0; i--) {
			const dayNum = daysInPrevMonth - i;
			const d = new Date(year, month - 1, dayNum, 12, 0, 0);
			const iso = toLocalIsoDate(d);
			const events = allEvents.filter((e: any) => e.date === iso);
			matrix.push({
				dayNumber: dayNum,
				isoDate: iso,
				isCurrentMonth: false,
				isToday: iso === todayIso,
				events
			});
		}

		// Jours du mois courant
		for (let dayNum = 1; dayNum <= daysInMonth; dayNum++) {
			const d = new Date(year, month, dayNum, 12, 0, 0);
			const iso = toLocalIsoDate(d);
			const events = allEvents.filter((e: any) => e.date === iso);
			matrix.push({
				dayNumber: dayNum,
				isoDate: iso,
				isCurrentMonth: true,
				isToday: iso === todayIso,
				events
			});
		}

		// Jours du mois suivant pour terminer la grille (jusqu'à multiple de 7)
		const remaining = (7 - (matrix.length % 7)) % 7;
		for (let dayNum = 1; dayNum <= remaining; dayNum++) {
			const d = new Date(year, month + 1, dayNum, 12, 0, 0);
			const iso = toLocalIsoDate(d);
			const events = allEvents.filter((e: any) => e.date === iso);
			matrix.push({
				dayNumber: dayNum,
				isoDate: iso,
				isCurrentMonth: false,
				isToday: iso === todayIso,
				events
			});
		}

		return matrix;
	});


</script>

<div class="space-y-6">
	<!-- En-tête : Titre, switcher de vue, et commandes de navigation temporelle -->
	<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-app-border">
		<div>
			<h1 class="text-xl font-bold text-fg tracking-tight">
				Emploi du temps
			</h1>
			<p class="text-xs text-muted mt-0.5">
				{viewMode === "week" ? weekRangeLabel() : monthLabel()}
			</p>
		</div>

		<div class="flex flex-wrap items-center gap-3">
			<!-- Légende discrète des types de cours -->
			<div class="hidden lg:flex items-center gap-2 text-[11px] text-muted mr-2">
				<span class="inline-flex items-center gap-1">
					<span class="w-2 h-2 rounded-full bg-c-tp"></span>
					<span>TP</span>
				</span>
				<span class="inline-flex items-center gap-1">
					<span class="w-2 h-2 rounded-full bg-c-td"></span>
					<span>TD</span>
				</span>
				<span class="inline-flex items-center gap-1">
					<span class="w-2 h-2 rounded-full bg-c-cm"></span>
					<span>CM</span>
				</span>
				<span class="inline-flex items-center gap-1">
					<span class="w-2 h-2 rounded-full bg-c-ds"></span>
					<span>DS</span>
				</span>
				<span class="inline-flex items-center gap-1">
					<span class="w-2 h-2 rounded-full bg-c-sae"></span>
					<span>SAÉ</span>
				</span>
			</div>

			<!-- Sélecteur de vue : Semaine / Mois -->
			<div class="flex items-center bg-app-card border border-app-border rounded-lg p-1 text-xs">
				<button
					type="button"
					onclick={() => (viewMode = "week")}
					class="px-3 py-1.5 rounded-md font-medium transition-colors cursor-pointer {viewMode === 'week' ? 'bg-app-raised text-fg' : 'text-muted hover:text-fg'}"
				>
					Semaine
				</button>
				<button
					type="button"
					onclick={() => (viewMode = "month")}
					class="px-3 py-1.5 rounded-md font-medium transition-colors cursor-pointer {viewMode === 'month' ? 'bg-app-raised text-fg' : 'text-muted hover:text-fg'}"
				>
					Mois
				</button>
			</div>

			<!-- Commandes de navigation temporelle (Semaine ou Mois) -->
			<div class="flex items-center bg-app-card border border-app-border rounded-lg p-1 text-xs">
				<button
					type="button"
					onclick={() => {
						if (viewMode === "week") weekOffset -= 1;
						else monthOffset -= 1;
					}}
					class="p-1.5 rounded-md text-muted hover:text-fg hover:bg-app-raised transition-colors cursor-pointer"
					title="Période précédente"
				>
					<ChevronLeft class="w-4 h-4" />
				</button>

				<button
					type="button"
					onclick={() => {
						if (viewMode === "week") weekOffset = 0;
						else monthOffset = 0;
					}}
					class="px-3 py-1 rounded-md text-xs font-semibold cursor-pointer transition-colors {(viewMode === 'week' && weekOffset === 0) || (viewMode === 'month' && monthOffset === 0) ? 'text-fg bg-app-raised' : 'text-muted hover:text-fg'}"
				>
					{#if viewMode === "week"}
						{weekOffset === 0 ? "Cette semaine" : `Semaine ${weekOffset > 0 ? '+' : ''}${weekOffset}`}
					{:else}
						{monthOffset === 0 ? "Ce mois" : monthLabel()}
					{/if}
				</button>

				<button
					type="button"
					onclick={() => {
						if (viewMode === "week") weekOffset += 1;
						else monthOffset += 1;
					}}
					class="p-1.5 rounded-md text-muted hover:text-fg hover:bg-app-raised transition-colors cursor-pointer"
					title="Période suivante"
				>
					<ChevronRight class="w-4 h-4" />
				</button>
			</div>

			<!-- Bouton Actualiser -->
			<button
				type="button"
				onclick={() => loadTimetable(true)}
				disabled={isLoading}
				class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-app-card hover:bg-app-raised border border-app-border text-xs font-medium text-muted hover:text-fg transition-all cursor-pointer"
			>
				<RefreshCw class="w-3.5 h-3.5 {isLoading ? 'animate-spin text-cyan-400' : ''}" />
				<span>Actualiser</span>
			</button>
		</div>
	</div>

	{#if isLoading && !timetableData}
		<Card class="space-y-4 p-5">
			<div class="flex items-center justify-between">
				<div class="space-y-1.5">
					<Skeleton class="h-4 w-48" />
					<Skeleton class="h-3 w-36" />
				</div>
				<Skeleton class="h-4 w-28 rounded-full" />
			</div>

			<!-- Grille des 5 jours Skeleton -->
			<div class="grid grid-cols-5 gap-3 pt-2">
				{#each Array(5) as _}
					<div class="space-y-3">
						<Skeleton class="h-10 w-full rounded-lg" />
						<div class="h-[480px] space-y-3">
							<Skeleton class="h-24 w-full rounded-md" />
							<Skeleton class="h-16 w-full rounded-md" />
							<Skeleton class="h-32 w-full rounded-md" />
						</div>
					</div>
				{/each}
			</div>
		</Card>
	{:else if error}
		<div class="p-4 rounded-lg bg-rose-900/40 text-rose-300 text-xs font-medium">
			{error}
		</div>
	{:else if timetableData}
		<!-- ==================================================== -->
		<!-- VUE SEMAINE : MÊME STYLE QUE LE TABLEAU DE BORD      -->
		<!-- ==================================================== -->
		{#if viewMode === "week"}
			<Card class="space-y-4">
				<!-- Mobile : agenda jour par jour (la grille horaire est illisible sur petit écran) -->
				<div class="md:hidden space-y-3" role="group" aria-label="Emploi du temps du jour" ontouchstart={onDayTouchStart} ontouchend={onDayTouchEnd}>
					<div class="flex items-center justify-between gap-2">
						<button
							type="button"
							onclick={() => stepMobileDay(-1)}
							aria-label="Jour précédent"
							class="p-2 rounded-lg border border-app-border bg-app-surface text-muted hover:text-fg cursor-pointer"
						>
							<ChevronLeft class="w-4 h-4" />
						</button>
						<div class="text-center min-w-0">
							<div class="text-sm font-bold text-fg capitalize truncate">{mobileDayLabel()}</div>
							{#if mobileDayIso === todayIso}
								<span class="text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-cyan-600/15 text-cyan-400">Aujourd'hui</span>
							{:else}
								<button type="button" onclick={() => setMobileDay(now.getDay() === 0 || now.getDay() === 6 ? nextWorkingDay(now, 1) : now)} class="text-[11px] font-medium text-cyan-400 cursor-pointer">
									Revenir à aujourd'hui
								</button>
							{/if}
						</div>
						<button
							type="button"
							onclick={() => stepMobileDay(1)}
							aria-label="Jour suivant"
							class="p-2 rounded-lg border border-app-border bg-app-surface text-muted hover:text-fg cursor-pointer"
						>
							<ChevronRight class="w-4 h-4" />
						</button>
					</div>

					{#if mobileDayEvents().length === 0}
						<div class="py-10 text-center text-xs text-muted">
							Aucun cours ce jour-là
						</div>
					{:else}
						<div class="space-y-1.5">
							{#each mobileDayEvents() as ev}
								<button
									type="button"
									onclick={() => openCourseDetail(ev)}
									class="w-full flex gap-3 text-left rounded-lg p-3 cursor-pointer {ev.colorStyle}"
								>
									<div class="text-[11px] font-bold shrink-0 leading-tight">
										{ev.start_time}<br /><span class="font-medium opacity-70">{ev.end_time}</span>
									</div>
									<div class="min-w-0">
										<div class="text-xs font-semibold">{ev.title}</div>
										<div class="text-[11px] opacity-80 truncate">{ev.location}{ev.teacher ? ` · ${ev.teacher}` : ""}</div>
									</div>
								</button>
							{/each}
						</div>
					{/if}
				</div>

				{#if weekEvents().length === 0}
					<div class="max-md:hidden py-16 text-center text-muted text-xs space-y-1">
						<p class="font-medium text-fg">Aucun cours programmé pour cette semaine.</p>
						<p class="text-subtle text-[11px]">Utilisez les flèches en haut pour naviguer vers d'autres semaines.</p>
					</div>
				{:else}
					<!-- Grille de la semaine avec axe des heures à gauche -->
					<div class="hidden md:block">
						<!-- En-têtes des jours de la semaine -->
						<div
							class="grid border-b border-app-border pb-2 text-center text-xs font-medium text-muted"
							style="grid-template-columns: 56px repeat({weekDays().length}, minmax(0, 1fr));"
						>
							<div class="text-left pl-1 text-subtle">Heure</div>
							{#each weekDays() as day}
								<div class="{day.isToday ? 'text-cyan-400 font-bold' : ''}">
									<span>{day.name}</span>
									<span class="block text-[10px] text-muted font-medium">{day.formattedDate}</span>
								</div>
							{/each}
						</div>

						<!-- Corps du calendrier : colonnes avec séparateurs fins -->
						<div
							class="relative h-[540px] grid divide-x divide-app-border"
							style="grid-template-columns: 56px repeat({weekDays().length}, minmax(0, 1fr));"
						>
							<!-- Axe des heures à gauche -->
							<div class="flex flex-col justify-between py-1 text-[10px] text-muted pr-2">
								<span>08:00</span>
								<span>09:30</span>
								<span>11:00</span>
								<span>12:30</span>
								<span>14:00</span>
								<span>15:30</span>
								<span>17:00</span>
								<span>18:30</span>
							</div>

							<!-- Colonnes des jours -->
							{#each weekDays() as day, dayIdx}
								<div class="relative h-full">
									<!-- Lignes de repère horizontales discrètes -->
									<div class="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-20">
										<div class="border-b border-app-border w-full"></div>
										<div class="border-b border-app-border w-full"></div>
										<div class="border-b border-app-border w-full"></div>
										<div class="border-b border-app-border w-full"></div>
										<div class="border-b border-app-border w-full"></div>
										<div class="border-b border-app-border w-full"></div>
										<div class="border-b border-app-border w-full"></div>
									</div>

									<!-- Ligne rouge de l'heure courante (jour actuel uniquement) -->
									{#if currentTimeIndicator() && currentTimeIndicator()?.dayIdx === dayIdx}
										<div
											class="absolute left-0 right-0 z-30 pointer-events-none flex items-center -translate-y-1/2"
											style="top: {currentTimeIndicator()?.topPercent}%;"
										>
											<div class="w-1.5 h-1.5 rounded-full bg-rose-500 -ml-1"></div>
											<div class="h-0.5 w-full bg-rose-500"></div>
											<span class="text-[9px] font-bold text-white bg-rose-600 px-1 py-0.5 rounded ml-0.5 whitespace-nowrap shadow-xs">
												{currentTimeIndicator()?.timeLabel}
											</span>
										</div>
									{/if}

									<!-- Cours de la journée -->
									{#each weekEvents().filter((e: any) => e.dayIdx === dayIdx) as ev}
										<button
											type="button"
											onclick={() => openCourseDetail(ev)}
											style="top: {ev.topPercent}%; height: {ev.heightPercent}%;"
											class="absolute left-1 right-1 rounded-lg p-2 text-xs text-left overflow-hidden shadow-sm transition-all hover:brightness-110 cursor-pointer z-10 {ev.colorStyle}"
										>
											<div class="flex items-center justify-between gap-1 mb-0.5">
												<span class="font-bold text-[10px] uppercase tracking-wider opacity-90">
													{ev.type}
												</span>
												<span class="text-[9px] font-medium opacity-90">
													{ev.start_time} - {ev.end_time}
												</span>
											</div>

											<div class="font-semibold truncate text-[11px] leading-tight">
												{ev.title}
											</div>

											{#if ev.location}
												<div class="text-[10px] opacity-80 truncate mt-0.5">
													{ev.location}
												</div>
											{/if}
										</button>
									{/each}
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</Card>

		<!-- ==================================================== -->
		<!-- VUE MOIS : CALENDRIER MENSUEL ÉPURÉ                 -->
		<!-- ==================================================== -->
		{:else}
			<Card class="space-y-4">
				<!-- Grille du calendrier mensuel -->
				<div class="overflow-hidden">
					<!-- En-têtes des jours (Lundi à Dimanche) -->
					<div class="grid grid-cols-7 border-b border-app-border text-center text-xs font-semibold text-muted py-2.5">
						<span>Lundi</span>
						<span>Mardi</span>
						<span>Mercredi</span>
						<span>Jeudi</span>
						<span>Vendredi</span>
						<span>Samedi</span>
						<span>Dimanche</span>
					</div>

					<!-- Grille des cellules de jours -->
					<div class="grid grid-cols-7 divide-x divide-y divide-app-border">
						{#each monthMatrix() as cell}
							<div class="min-h-[110px] p-2 flex flex-col justify-between transition-colors {cell.isCurrentMonth ? '' : 'opacity-40'} {cell.isToday ? 'bg-cyan-600/10' : ''}">
								<div class="flex items-center justify-between mb-1.5">
									<span class="text-xs font-bold {cell.isToday ? 'bg-cyan-600 text-white w-5 h-5 rounded-full flex items-center justify-center text-[10px]' : cell.isCurrentMonth ? 'text-fg' : 'text-subtle'}">
										{cell.dayNumber}
									</span>
								</div>

								<!-- Liste miniature des cours du jour -->
								<div class="space-y-1 flex-1 overflow-hidden">
									{#each cell.events.slice(0, 3) as ev}
										<button
											type="button"
											onclick={() => openCourseDetail(ev)}
											class="w-full text-left px-1.5 py-0.5 rounded text-[10px] font-medium truncate block transition-all hover:brightness-110 cursor-pointer {getCourseColorStyle(ev.type)}"
											title="{ev.start_time} - {ev.title} ({ev.location})"
										>
											<span class="font-bold mr-1">{ev.start_time}</span>
											<span>{ev.title}</span>
										</button>
									{/each}

									{#if cell.events.length > 3}
										<span class="block text-[9px] text-muted text-center font-medium pt-0.5">
											+ {cell.events.length - 3} autres
										</span>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				</div>
			</Card>
		{/if}
	{/if}
</div>

<CourseDetailModal course={selectedCourse} bind:open={isModalOpen} events={timetableData?.all_events} onAddTask={onAddTaskForCourse} />
