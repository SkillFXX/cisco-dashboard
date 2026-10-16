<script lang="ts">
	import { onMount } from "svelte";
	import { api } from "$lib/api";
	import { formatGrade, formatDateFr } from "$lib/utils";
	import {
		Plus,
		Check,
		Square,
		CheckSquare2,
		Clock,
		Calendar,
		Sparkles,
		RefreshCw,
		ArrowUpRight,
		MapPin,
		User as UserIcon,
		AlertCircle
	} from "lucide-svelte";

	let {
		onOpenAddTask,
		onNavigate
	}: {
		onOpenAddTask?: () => void;
		onNavigate?: (tab: string) => void;
	} = $props();

	let overview = $state<any>(null);
	let isLoading = $state(true);
	let error = $state("");
	let isRefreshing = $state(false);

	// Load Overview Data
	async function loadOverview(silent = false) {
		if (!silent) isLoading = true;
		error = "";
		try {
			overview = await api.getDashboardOverview();
		} catch (err: any) {
			error = err.message || "Erreur lors du chargement des données.";
		} finally {
			isLoading = false;
			isRefreshing = false;
		}
	}

	async function toggleTaskStatus(task: any) {
		if (task.is_personal) {
			try {
				const newStatus = task.status === "done" ? "todo" : "done";
				await api.updateTask(task.task_id, { status: newStatus });
				await loadOverview(true);
			} catch (e) {
				console.error(e);
			}
		} else {
			// For moodle tasks, toggle UI state locally
			task.done = !task.done;
		}
	}

	onMount(() => {
		loadOverview();
	});

	// GPA Calculation for Donut Progress Ring
	let gpaValue = $derived(() => {
		const val = overview?.stats?.moyenne_generale;
		if (typeof val === "number" && !isNaN(val)) return val;
		return 16.26; // Default demo / user GPA
	});

	// Circular Gauge constants
	const radius = 28;
	const circumference = 2 * Math.PI * radius;
	let strokeDashoffset = $derived(() => {
		const score = gpaValue();
		const ratio = Math.min(Math.max(score / 20, 0), 1);
		return circumference * (1 - ratio);
	});

	// Absences stats
	let unjustifiedCount = $derived(() => {
		return overview?.absences?.injustifiees_nb ?? 0;
	});

	// Next Class info
	let nextClass = $derived(() => {
		if (overview?.current_course) {
			return {
				title: `${overview.current_course.title} (En cours)`,
				subtitle: `${overview.current_course.location || "Lab 3"} • ${overview.current_course.teacher || "Enseignant RT"}`,
				highlight: "EN COURS",
				time: `${overview.current_course.start_time} - ${overview.current_course.end_time}`
			};
		}
		if (overview?.next_course) {
			return {
				title: `${overview.next_course.title}`,
				subtitle: `${overview.next_course.location || "Salle 204"} • ${overview.next_course.teacher || "M. Dubois"}`,
				highlight: `À ${overview.next_course.start_time}`,
				time: `${overview.next_course.day_name || "Aujourd'hui"} ${overview.next_course.start_time}`
			};
		}
		return {
			title: "ROUTING LAB in 14 mins",
			subtitle: "Room 204 • M. Dubois",
			highlight: "in 14 mins",
			time: "14:00 - 16:00"
		};
	});

	// Weekly schedule helper: 5 days (Mon-Fri)
	const weekDays = [
		{ key: "Mon", label: "Mon", fr: "Lundi", offset: 0 },
		{ key: "Tue", label: "Tue", fr: "Mardi", offset: 1 },
		{ key: "Wed", label: "Wed", fr: "Mercredi", offset: 2 },
		{ key: "Thu", label: "Thu", fr: "Jeudi", offset: 3 },
		{ key: "Fri", label: "Fri", fr: "Vendredi", offset: 4 }
	];

	// Current day index (0 = Monday, ..., 4 = Friday)
	const currentDayIndex = new Date().getDay() - 1; // 0 is Mon in France

	// Time slots from 8h to 18h (in minutes from 08:00: total 600 mins)
	const startHour = 8;
	const endHour = 18;
	const totalMinutes = (endHour - startHour) * 60; // 600

	function timeToMinutes(timeStr: string): number {
		if (!timeStr) return 0;
		const parts = timeStr.split(":");
		const h = parseInt(parts[0], 10);
		const m = parseInt(parts[1] || "0", 10);
		return (h - startHour) * 60 + m;
	}

	// Dynamic or Mock schedule events
	let weeklyScheduleEvents = $derived(() => {
		const rawEvents = overview?.timetable_events || overview?.today_schedule || [];
		if (rawEvents.length > 0) {
			// Map real events
			return rawEvents.slice(0, 12).map((e: any, idx: number) => {
				const startMins = timeToMinutes(e.start_time);
				const endMins = timeToMinutes(e.end_time);
				const duration = Math.max(endMins - startMins, 60);

				// Assign color palette
				const colors = [
					"bg-[#00C9A7] text-black border-[#00C9A7]/40",
					"bg-[#8B5CF6] text-white border-[#8B5CF6]/40",
					"bg-[#F97316] text-white border-[#F97316]/40",
					"bg-[#10B981] text-white border-[#10B981]/40"
				];
				const colorClass = colors[idx % colors.length];

				// Day offset (0 = Mon, 4 = Fri)
				let dayIdx = 0;
				if (e.date) {
					const d = new Date(e.date);
					dayIdx = (d.getDay() + 6) % 7; // Monday = 0
				}

				return {
					id: e.id || idx,
					title: e.title || "Cours RT",
					location: e.location || "Lab 3",
					time: `${e.start_time} - ${e.end_time}`,
					dayIdx: Math.min(Math.max(dayIdx, 0), 4),
					topPercent: Math.min(Math.max((startMins / totalMinutes) * 100, 2), 85),
					heightPercent: Math.min(Math.max((duration / totalMinutes) * 100, 12), 45),
					colorClass
				};
			});
		}

		// Clean default mockup events matching the user image
		return [
			{
				id: 1,
				title: "IP Routing Lab",
				location: "Lab 3",
				time: "11:00 - 13:00",
				dayIdx: 0, // Mon
				topPercent: 28,
				heightPercent: 24,
				colorClass: "bg-[#06B6D4] text-white border-[#06B6D4]/30"
			},
			{
				id: 2,
				title: "Optical Fiber Physics",
				location: "Lab 3",
				time: "15:00 - 18:00",
				dayIdx: 2, // Wed
				topPercent: 42,
				heightPercent: 22,
				colorClass: "bg-[#8B5CF6] text-white border-[#8B5CF6]/30"
			},
			{
				id: 3,
				title: "Cybersecurity/VPN",
				location: "Lab 3",
				time: "13:00 - 17:00",
				dayIdx: 1, // Tue
				topPercent: 55,
				heightPercent: 22,
				colorClass: "bg-[#F97316] text-white border-[#F97316]/30"
			},
			{
				id: 4,
				title: "Cybersecurity VPN",
				location: "Lab 3",
				time: "14:00 - 16:00",
				dayIdx: 3, // Thu
				topPercent: 48,
				heightPercent: 18,
				colorClass: "bg-[#F59E0B] text-black border-[#F59E0B]/30"
			},
			{
				id: 5,
				title: "Linux Admin",
				location: "Lab 3",
				time: "11:00 - 18:00",
				dayIdx: 4, // Fri
				topPercent: 52,
				heightPercent: 24,
				colorClass: "bg-[#10B981] text-white border-[#10B981]/30"
			}
		];
	});

	// Upcoming deadlines & tasks
	let deadlineItems = $derived(() => {
		const tasks = overview?.upcoming_tasks || [];
		if (tasks.length > 0) {
			return tasks.slice(0, 6).map((t: any) => ({
				id: t.id,
				title: t.is_personal ? `${t.type === 'ds' ? 'DS:' : 'Devoir:'} ${t.title}` : `Moodle: ${t.title}`,
				isUrgent: t.days_left <= 2,
				badge: t.days_left <= 2 ? "Urgent" : null,
				subtitle: t.days_left === 0 ? "Due Today, 23:59" : t.days_left === 1 ? "Demain" : `Dans ${t.days_left} jours (${formatDateFr(t.due_date)})`,
				done: t.status === "done",
				isPersonal: t.is_personal,
				raw: t
			}));
		}

		// Default items matching mockup
		return [
			{
				id: "m-1",
				title: "Moodle: Router Conf",
				isUrgent: true,
				badge: "Urgent",
				subtitle: "Due Today, 23:59",
				done: false,
				isPersonal: false
			},
			{
				id: "m-2",
				title: "DS: Signal Theory",
				isUrgent: false,
				badge: null,
				subtitle: "(Fri, 10:00)",
				done: false,
				isPersonal: true
			},
			{
				id: "m-3",
				title: "Lab Report: VoIP",
				isUrgent: false,
				badge: null,
				subtitle: "(Oct 20)",
				done: false,
				isPersonal: false
			}
		];
	});

	// Recent grades list
	let recentGradesList = $derived(() => {
		const grades = overview?.recent_grades || [];
		if (grades.length > 0) {
			return grades.slice(0, 4).map((g: any) => ({
				subject: g.matiere_nom || g.matiere || "Module RT",
				type: g.type || (g.nom?.toUpperCase().includes("TP") ? "TP" : g.nom?.toUpperCase().includes("DS") ? "DS" : "TD"),
				date: g.date ? formatDateFr(g.date) : "Octobre",
				score: formatGrade(g.note)
			}));
		}

		// Mockup grades
		return [
			{ subject: "Réseaux LAN (IP Routing)", type: "TD", date: "Oct 12", score: "18.5/20" },
			{ subject: "Télécom (Signals)", type: "DS", date: "Oct 08", score: "12.0/20" },
			{ subject: "Maths (Fourier)", type: "CC", date: "Oct 05", score: "15.0/20" },
			{ subject: "Linux & Shell", type: "TP", date: "Sep 29", score: "17.0/20" }
		];
	});
</script>

<div class="space-y-6">
	<!-- Top Row: 3 Metric Cards -->
	<div class="grid grid-cols-1 sm:grid-cols-3 gap-5">
		<!-- KPI 1 : Overall GPA -->
		<div class="bg-[#121622] border border-[#1E2536] rounded-2xl p-5 flex items-center justify-between relative overflow-hidden group hover:border-cyan-500/40 transition-all shadow-sm">
			<div class="space-y-2">
				<div class="space-y-0.5">
					<h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Overall GPA</h3>
					<p class="text-xs text-zinc-500">Moyenne générale</p>
				</div>
				<div class="flex items-baseline gap-1">
					<span class="text-3xl font-extrabold text-white tracking-tight font-mono">
						{gpaValue().toFixed(2)}
					</span>
					<span class="text-sm font-semibold text-zinc-500">/20</span>
				</div>
				<div class="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
					<span>↗</span>
					<span>
						{overview?.stats?.rang ? `Rang #${overview.stats.rang}/${overview.stats.total_promo || 66} promo` : "+0.4 this semester"}
					</span>
				</div>
			</div>

			<!-- Circular Donut Ring Gauge -->
			<div class="relative w-18 h-18 flex items-center justify-center shrink-0">
				<svg class="w-18 h-18 -rotate-90" viewBox="0 0 72 72">
					<!-- Background track -->
					<circle
						cx="36"
						cy="36"
						r={radius}
						fill="transparent"
						stroke="#1C2230"
						stroke-width="5"
					/>
					<!-- Glowing progress arc -->
					<circle
						cx="36"
						cy="36"
						r={radius}
						fill="transparent"
						stroke="#00C9A7"
						stroke-width="5"
						stroke-linecap="round"
						stroke-dasharray={circumference}
						stroke-dashoffset={strokeDashoffset()}
						class="transition-all duration-700 ease-out"
					/>
				</svg>
			</div>
		</div>

		<!-- KPI 2 : Unjustified Absences -->
		<div class="bg-[#121622] border border-[#1E2536] rounded-2xl p-5 flex flex-col justify-between group hover:border-amber-500/40 transition-all shadow-sm">
			<div class="space-y-0.5">
				<h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Unjustified Absences</h3>
				<p class="text-xs text-zinc-500">Absences non justifiées</p>
			</div>

			<div class="my-2">
				<span class="text-3xl font-extrabold text-white tracking-tight font-mono">
					{unjustifiedCount()}
				</span>
			</div>

			<div>
				{#if unjustifiedCount() > 0}
					<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-[#2B1B17] text-[#FB923C] border border-[#7C2D12]">
						Needs Justification
					</span>
				{:else}
					<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-[#11241E] text-[#34D399] border border-[#065F46]">
						✓ Tout est justifié
					</span>
				{/if}
			</div>
		</div>

		<!-- KPI 3 : Next Class -->
		<div class="bg-[#121622] border border-[#1E2536] rounded-2xl p-5 flex flex-col justify-between group hover:border-cyan-500/40 transition-all shadow-sm">
			<div class="space-y-0.5">
				<h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-400">Next Class</h3>
				<p class="text-xs text-zinc-500">Prochain cours programmé</p>
			</div>

			<div class="my-1.5 space-y-1">
				<div class="text-base font-bold text-white truncate" title={nextClass().title}>
					{nextClass().title}
				</div>
				<div class="text-xs text-zinc-400 truncate">
					{nextClass().subtitle}
				</div>
			</div>

			<div class="flex items-center justify-between text-xs text-zinc-500 border-t border-[#1C212D] pt-2.5">
				<span>{nextClass().time}</span>
				{#if onNavigate}
					<button
						onclick={() => onNavigate("timetable")}
						class="text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-0.5 cursor-pointer text-[11px]"
					>
						Emploi du temps <ArrowUpRight class="w-3 h-3" />
					</button>
				{/if}
			</div>
		</div>
	</div>

	<!-- Middle Row: 2-Column Split (Weekly Timetable + Upcoming Deadlines) -->
	<div class="grid grid-cols-1 md:grid-cols-12 gap-5">
		<!-- Left: Weekly Timetable Schedule (2/3 cols) -->
		<div class="md:col-span-8 bg-[#121622] border border-[#1E2536] rounded-2xl p-5 space-y-4">
			<div class="flex items-center justify-between">
				<div>
					<h2 class="text-sm font-bold text-white">Weekly Timetable Schedule (Emploi du temps)</h2>
				</div>
				{#if onNavigate}
					<button
						onclick={() => onNavigate("timetable")}
						class="text-xs text-cyan-400 hover:underline flex items-center gap-1 cursor-pointer font-medium"
					>
						Voir semaine complète <ArrowUpRight class="w-3 h-3" />
					</button>
				{/if}
			</div>

			<!-- Visual Interactive Weekly Timetable Grid -->
			<div class="relative bg-[#0E121A] border border-[#1C2230] rounded-xl p-3 select-none overflow-hidden">
				<!-- Day Columns Header -->
				<div class="grid grid-cols-6 border-b border-[#1C2230] pb-2 text-center text-xs font-medium text-zinc-400">
					<!-- Time column header -->
					<div class="text-left pl-1 text-zinc-500">Heure</div>
					{#each weekDays as day, i}
						<div class="{currentDayIndex === i ? 'text-cyan-400 font-bold' : ''}">
							{day.label}
						</div>
					{/each}
				</div>

				<!-- Calendar Body with Hours on the Left and 5 Day Slots -->
				<div class="relative h-80 grid grid-cols-6 divide-x divide-[#1C2230]">
					<!-- Time Ticks on the left -->
					<div class="flex flex-col justify-between py-1 text-[10px] font-mono text-zinc-500 pr-2">
						<span>8:00</span>
						<span>9:00</span>
						<span>10:00</span>
						<span>11:00</span>
						<span>12:00</span>
						<span>14:00</span>
						<span>16:00</span>
						<span>17:00</span>
						<span>18:00</span>
					</div>

					<!-- 5 Day Columns -->
					{#each weekDays as day, dayIdx}
						<div class="relative h-full">
							<!-- Horizontal hour grid lines -->
							<div class="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-20">
								<div class="border-b border-zinc-700 w-full"></div>
								<div class="border-b border-zinc-700 w-full"></div>
								<div class="border-b border-zinc-700 w-full"></div>
								<div class="border-b border-zinc-700 w-full"></div>
								<div class="border-b border-zinc-700 w-full"></div>
								<div class="border-b border-zinc-700 w-full"></div>
								<div class="border-b border-zinc-700 w-full"></div>
								<div class="border-b border-zinc-700 w-full"></div>
							</div>

							<!-- Current Time Red Line Indicator (if today) -->
							{#if currentDayIndex === dayIdx}
								<div class="absolute inset-y-0 left-1/2 w-0.5 bg-red-500/80 pointer-events-none z-20 flex flex-col items-center">
									<span class="text-[9px] font-bold text-red-400 bg-red-950/80 px-1 py-0.5 rounded border border-red-500/30 whitespace-nowrap mt-1">
										Current Time
									</span>
								</div>
							{/if}

							<!-- Events in this day -->
							{#each weeklyScheduleEvents().filter((e) => e.dayIdx === dayIdx) as ev}
								<div
									style="top: {ev.topPercent}%; height: {ev.heightPercent}%;"
									class="absolute left-1 right-1 rounded-lg p-2 text-xs font-sans shadow-md border overflow-hidden transition-transform hover:scale-[1.02] cursor-pointer z-10 {ev.colorClass}"
									title="{ev.title} ({ev.time}) - {ev.location}"
								>
									<div class="font-bold truncate text-[11px] leading-tight">
										{ev.title}
									</div>
									<div class="text-[10px] opacity-80 truncate mt-0.5">
										{ev.location}
									</div>
									<div class="text-[9px] opacity-75 font-mono mt-0.5">
										{ev.time}
									</div>
								</div>
							{/each}
						</div>
					{/each}
				</div>
			</div>
		</div>

		<!-- Right: Upcoming Deadlines & Exams (1/3 col) -->
		<div class="md:col-span-4 bg-[#121622] border border-[#1E2536] rounded-2xl p-5 flex flex-col justify-between space-y-4">
			<div>
				<div class="space-y-0.5 mb-3">
					<h2 class="text-sm font-bold text-white">Upcoming Deadlines & Exams</h2>
					<p class="text-xs text-zinc-500">Merge Moodle tasks and exams</p>
				</div>

				<!-- Task Checklist -->
				<div class="space-y-2.5">
					{#each deadlineItems() as item}
						<div
							class="flex items-start gap-3 p-3 rounded-xl bg-[#0E121A] border border-[#1C2230] hover:border-zinc-700 transition-all group"
						>
							<!-- Checkbox button -->
							<button
								onclick={() => toggleTaskStatus(item.raw || item)}
								class="mt-0.5 text-zinc-500 hover:text-cyan-400 transition-colors cursor-pointer shrink-0"
								title="Marquer comme fait"
							>
								{#if item.done}
									<CheckSquare2 class="w-4 h-4 text-cyan-400" />
								{:else}
									<Square class="w-4 h-4 text-zinc-500 group-hover:text-zinc-300" />
								{/if}
							</button>

							<div class="space-y-1 flex-1 min-w-0">
								<div class="flex items-center gap-2 flex-wrap">
									<span class="text-xs font-semibold text-zinc-200 truncate {item.done ? 'line-through text-zinc-500' : ''}">
										{item.title}
									</span>
									{#if item.isUrgent}
										<span class="px-1.5 py-0.2 rounded text-[10px] font-bold bg-red-500/15 text-red-400 border border-red-500/30">
											Urgent
										</span>
									{/if}
								</div>
								<div class="text-[11px] text-zinc-500">
									{item.subtitle}
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Add Task Button -->
			{#if onOpenAddTask}
				<button
					onclick={onOpenAddTask}
					class="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl border border-dashed border-[#232A3B] hover:border-cyan-500/50 bg-[#0E121A] hover:bg-[#151B27] text-xs font-semibold text-zinc-300 hover:text-white transition-all cursor-pointer shadow-sm"
				>
					<Plus class="w-4 h-4 text-cyan-400" />
					<span>+ Add Task</span>
				</button>
			{/if}
		</div>
	</div>

	<!-- Bottom Row: Recent Grades Table -->
	<div class="bg-[#121622] border border-[#1E2536] rounded-2xl p-5 space-y-4 shadow-sm">
		<div class="flex items-center justify-between">
			<h2 class="text-sm font-bold text-white">Recent Grades</h2>
			{#if onNavigate}
				<button
					onclick={() => onNavigate("grades")}
					class="text-xs text-cyan-400 hover:underline flex items-center gap-1 cursor-pointer font-medium"
				>
					Voir tout ScoDoc <ArrowUpRight class="w-3 h-3" />
				</button>
			{/if}
		</div>

		<!-- Table -->
		<div class="overflow-x-auto rounded-xl border border-[#1C2230]">
			<table class="w-full text-left text-xs">
				<thead class="bg-[#0E121A] text-zinc-400 border-b border-[#1C2230] font-medium">
					<tr>
						<th class="py-3 px-4">Subject</th>
						<th class="py-3 px-4">Type</th>
						<th class="py-3 px-4">Date</th>
						<th class="py-3 px-4 text-right">Score</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-[#1C2230] bg-[#121622]/60">
					{#each recentGradesList() as grade}
						<tr class="hover:bg-[#161C2A] transition-colors">
							<td class="py-3 px-4 font-semibold text-zinc-200">
								{grade.subject}
							</td>
							<td class="py-3 px-4 text-zinc-400">
								<span class="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono text-[11px]">
									{grade.type}
								</span>
							</td>
							<td class="py-3 px-4 text-zinc-400 font-mono text-[11px]">
								{grade.date}
							</td>
							<td class="py-3 px-4 text-right">
								<span class="inline-block px-2.5 py-0.5 rounded font-mono font-bold text-xs bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-[0_0_10px_rgba(6,182,212,0.15)]">
									{grade.score}
								</span>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>
</div>
