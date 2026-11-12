<script lang="ts">
	import Card from "./Card.svelte";
	import Badge from "./Badge.svelte";
	import AverageCard from "./AverageCard.svelte";
	import { navItems } from "$lib/nav";
	import { getCourseColorStyle } from "$lib/utils";

	// Maquette décorative du tableau de bord (données fictives) : reprend les vrais composants, donc reste nette et suit le thème.
	const nav = navItems.filter((i) => !i.adminOnly);
	const stats = { moyenne_generale: 12.78, min_promo: 5.1, moy_promo: 11.4, max_promo: 17.2 };
	const series = [11.2, 11.5, 11.4, 11.9, 12.1, 12.0, 12.4, 12.5, 12.78];

	const days = [
		{ name: "Lun", date: "9 / 11" },
		{ name: "Mar", date: "10 / 11" },
		{ name: "Mer", date: "11 / 11" },
		{ name: "Jeu", date: "12 / 11", today: true },
		{ name: "Ven", date: "13 / 11" }
	];
	const hours = ["08:00", "09:30", "11:00", "12:30", "14:00", "15:30", "17:00"];
	// start / end en heures décimales (plage affichée : 8 h - 18 h)
	const courses = [
		{ day: 0, start: 8.5, end: 10, type: "CM", title: "R101 Initiation aux réseaux", room: "D015" },
		{ day: 0, start: 10.25, end: 11.75, type: "TD", title: "R104 Électronique", room: "C211" },
		{ day: 1, start: 9, end: 10.5, type: "TP", title: "R110 Anglais", room: "A104" },
		{ day: 1, start: 13.5, end: 16.75, type: "TP", title: "R107 Programmation", room: "B207" },
		{ day: 2, start: 8.5, end: 10, type: "CM", title: "R101 Initiation aux réseaux", room: "D015" },
		{ day: 2, start: 14, end: 16, type: "DS", title: "R113 Maths du signal", room: "D015" },
		{ day: 3, start: 10.25, end: 11.75, type: "TD", title: "R104 Électronique", room: "C211" },
		{ day: 3, start: 13.5, end: 16.75, type: "TP", title: "R107 Programmation", room: "B207" },
		{ day: 4, start: 9, end: 10.5, type: "TP", title: "R110 Anglais", room: "A104" },
		{ day: 4, start: 14, end: 16, type: "DS", title: "R113 Maths du signal", room: "D015" }
	];
	// Mise à l'échelle : la maquette (1180 px de large) garde ses proportions quelle que soit la taille de la colonne
	const DESIGN_WIDTH = 1180;
	let width = $state(0);
	let height = $state(0);
	let scale = $derived(Math.max(0.55, Math.min(1.1, (width + 16) / DESIGN_WIDTH)));

	const RANGE_START = 8;
	const RANGE = 10;

	const grades = [
		{ title: "DS 1 - Modèle OSI", code: "R101", date: "10 nov.", note: "14,5", promo: "11,2" },
		{ title: "TP noté - Packet Tracer", code: "R101", date: "08 nov.", note: "16", promo: "12,8" },
		{ title: "Projet Python", code: "R107", date: "05 nov.", note: "17", promo: "13,2" },
		{ title: "DS Électronique", code: "R104", date: "03 nov.", note: "12", promo: "10,9" },
		{ title: "Oral d'anglais", code: "R110", date: "30 oct.", note: "15", promo: "13,5" },
		{ title: "DS 1 - Adressage IPv4", code: "R102", date: "27 oct.", note: "9,5", promo: "10,4" }
	];

	const tasks = [
		{ title: "R113 Maths du signal", kind: "DS", when: "Demain", variant: "warning" as const },
		{ title: "DS Réseaux - OSPF", kind: "DS", when: "Dans 2 j", variant: "secondary" as const },
		{ title: "Rendre le TP Python", kind: "TP", when: "Dans 4 j", variant: "secondary" as const },
		{ title: "Réviser maths", kind: "À faire", when: "Dans 6 j", variant: "secondary" as const }
	];
</script>

<div class="preview absolute inset-0 select-none pointer-events-none" aria-hidden="true" bind:clientWidth={width} bind:clientHeight={height}>
	<div
		class="frame absolute left-0 origin-top-left rounded-tl-2xl border border-r-0 border-app-border bg-app-bg shadow-2xl"
		style="width: {DESIGN_WIDTH}px; top: {height * 0.06}px; height: {(height * 0.94) / scale}px; transform: scale({scale});"
	>
		<div class="flex h-full">
			<!-- Barre latérale -->
			<div class="w-52 shrink-0 border-r border-app-border p-3 space-y-5">
				<div class="flex items-center gap-2.5 px-1 pt-1">
					<img src="/icon.png" alt="" class="w-8 h-8 rounded-lg" />
					<span class="font-extrabold text-base tracking-tight text-fg">Cisco</span>
				</div>
				<div class="space-y-1">
					{#each nav as item, i}
						{@const Icon = item.icon}
						<div class="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium {i === 0 ? 'bg-app-raised text-fg' : 'text-muted'}">
							<Icon class="w-4 h-4" />
							{item.label}
						</div>
					{/each}
				</div>
			</div>

			<!-- Contenu -->
			<div class="flex-1 min-w-0 p-6 space-y-4">
				<div class="flex items-center justify-between">
					<div class="text-xs text-muted">Tableau de bord <span class="text-subtle">/</span> <span class="text-fg font-medium">Vue d'ensemble</span></div>
					<div class="rounded-lg bg-cyan-600 text-white text-xs font-semibold px-3.5 py-1.5">+ Nouveau DS / Devoir</div>
				</div>

				<div class="grid grid-cols-3 gap-4">
					<AverageCard {stats} {series} />
					<Card class="p-4 space-y-2">
						<span class="text-[11px] font-semibold uppercase tracking-wider text-muted">Absences non justifiées</span>
						<div class="flex items-baseline gap-1.5">
							<span class="text-3xl font-black text-fg">1</span>
							<span class="text-xs text-subtle font-semibold">demi-journée</span>
						</div>
						<div class="pt-1.5 border-t border-app-border"><Badge variant="destructive">À justifier</Badge></div>
					</Card>
					<Card class="p-4 space-y-2">
						<span class="text-[11px] font-semibold uppercase tracking-wider text-muted">Prochain cours</span>
						<p class="text-base font-bold text-fg leading-tight">R110 Anglais</p>
						<p class="text-xs text-muted">A104 • Soldevila Lauren</p>
						<div class="pt-1.5 border-t border-app-border flex items-center justify-between text-[11px] text-muted">
							<span>Vendredi à 09:00</span><span>09:00 - 10:30</span>
						</div>
					</Card>
				</div>

				<div class="grid grid-cols-12 gap-4">
					<Card class="col-span-8 space-y-3">
						<h2 class="text-sm font-bold text-fg">Cette semaine</h2>
						<div class="grid grid-cols-6 border-b border-app-border pb-2 text-center text-xs font-medium text-muted">
							<div class="text-left pl-1 text-subtle">Heure</div>
							{#each days as d}
								<div>
									<span class={d.today ? "rounded-md bg-cyan-600/15 text-cyan-400 px-2 py-0.5 font-semibold" : ""}>{d.name}</span>
									<span class="block text-[10px] text-subtle">{d.date}</span>
								</div>
							{/each}
						</div>
						<div class="relative h-80 grid grid-cols-6 divide-x divide-app-border">
							<div class="flex flex-col justify-between py-1 text-[10px] text-subtle pr-2">
								{#each hours as h}<span>{h}</span>{/each}
							</div>
							{#each days as _, dayIdx}
								<div class="relative h-full">
									{#each courses.filter((c) => c.day === dayIdx) as c}
										<div
											class="absolute inset-x-1 rounded-md px-2 py-1 overflow-hidden {getCourseColorStyle(c.type)}"
											style="top: {((c.start - RANGE_START) / RANGE) * 100}%; height: {((c.end - c.start) / RANGE) * 100}%;"
										>
											<p class="text-[11px] font-bold leading-tight line-clamp-2">{c.title}</p>
											<p class="text-[10px] text-muted mt-0.5">{c.room}</p>
										</div>
									{/each}
								</div>
							{/each}
						</div>
					</Card>

					<Card class="col-span-4 space-y-3">
						<h2 class="text-sm font-bold text-fg">Devoirs à venir</h2>
						<div class="space-y-3">
							{#each tasks as t}
								<div class="flex items-center gap-3">
									<span class="w-4 h-4 rounded-full border border-subtle shrink-0"></span>
									<div class="min-w-0 flex-1">
										<p class="text-sm font-semibold text-fg truncate">{t.title}</p>
										<p class="text-[11px] text-subtle">{t.kind}</p>
									</div>
									<Badge variant={t.variant}>{t.when}</Badge>
								</div>
							{/each}
						</div>
					</Card>
				</div>

				<Card class="space-y-3">
					<h2 class="text-sm font-bold text-fg">Dernières notes</h2>
					<div class="divide-y divide-app-border">
						{#each grades as g}
							<div class="flex items-center gap-3 py-2.5">
								<Badge variant="secondary">{g.code}</Badge>
								<p class="text-sm text-fg flex-1 truncate">{g.title}</p>
								<span class="text-xs text-subtle w-14">{g.date}</span>
								<span class="text-xs text-subtle w-20 text-right">promo {g.promo}</span>
								<span class="text-sm font-bold text-fg w-10 text-right">{g.note}</span>
							</div>
						{/each}
					</div>
				</Card>
			</div>
		</div>
	</div>
</div>

<style>
	/* Fondu vers le formulaire (à gauche) et vers le bas : l'aperçu se dissout dans la page */
	.preview {
		-webkit-mask-image: linear-gradient(to right, transparent 0%, #000 12%), linear-gradient(to bottom, #000 80%, transparent 100%);
		mask-image: linear-gradient(to right, transparent 0%, #000 12%), linear-gradient(to bottom, #000 80%, transparent 100%);
		-webkit-mask-composite: source-in;
		mask-composite: intersect;
	}
</style>
