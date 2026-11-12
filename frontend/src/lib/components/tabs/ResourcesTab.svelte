<script lang="ts">
	import { onMount } from "svelte";
	import Card from "../Card.svelte";
	import Badge from "../Badge.svelte";
	import Skeleton from "../Skeleton.svelte";
	import { api } from "$lib/api";
	import {
		ArrowLeft,
		BookOpen,
		ChevronDown,
		Download,
		ExternalLink,
		Eye,
		File,
		FileArchive,
		FileCode,
		FileImage,
		FileSpreadsheet,
		FileText,
		Folder,
		Link2,
		Presentation,
		RefreshCw,
		Search
	} from "lucide-svelte";

	let { onNavigate }: { onNavigate?: (tab: string) => void } = $props();

	const LAST_COURSE_KEY = "cisco_resources_course";

	let courses = $state<any[]>([]);
	let configured = $state(true);
	let listError = $state("");
	let loadingList = $state(true);

	let selectedId = $state<number | null>(null);
	let course = $state<any>(null);
	let courseError = $state("");
	let loadingCourse = $state(false);

	let courseQuery = $state("");
	let query = $state("");
	let collapsed = $state<Set<number>>(new Set());
	let busyFile = $state<string | null>(null);
	let fileError = $state("");

	let selectedCourse = $derived(courses.find((c) => c.id === selectedId) ?? null);
	let filteredCourses = $derived.by(() => {
		const q = courseQuery.trim().toLowerCase();
		return q ? courses.filter((c) => `${c.fullname} ${c.shortname}`.toLowerCase().includes(q)) : courses;
	});

	// Sections filtrees par la recherche (nom du document, du fichier ou du bloc)
	let visibleSections = $derived.by(() => {
		const sections: any[] = course?.sections ?? [];
		const q = query.trim().toLowerCase();
		if (!q) return sections;
		return sections
			.map((sec) => ({
				...sec,
				modules: sec.modules.filter(
					(m: any) =>
						sec.name.toLowerCase().includes(q) ||
						m.name.toLowerCase().includes(q) ||
						m.files.some((f: any) => f.name.toLowerCase().includes(q))
				)
			}))
			.filter((sec) => sec.modules.length);
	});

	async function loadCourses(force = false) {
		loadingList = true;
		listError = "";
		try {
			const res = await api.getResourceCourses(force);
			configured = res.configured;
			courses = res.courses ?? [];
			listError = res.error ?? "";
			if (selectedId === null) {
				const saved = Number(sessionStorage.getItem(LAST_COURSE_KEY));
				if (saved && courses.some((c) => c.id === saved)) void selectCourse(saved);
			}
		} catch (e: any) {
			listError = e.message || "Impossible de charger les cours.";
		} finally {
			loadingList = false;
		}
	}

	async function selectCourse(id: number, force = false) {
		selectedId = id;
		try {
			sessionStorage.setItem(LAST_COURSE_KEY, String(id));
		} catch {
			// stockage indisponible
		}
		if (!force) {
			query = "";
			collapsed = new Set();
		}
		loadingCourse = true;
		courseError = "";
		fileError = "";
		try {
			const res = await api.getResourceCourse(id, force);
			course = res;
			courseError = res.error ?? "";
		} catch (e: any) {
			course = null;
			courseError = e.message || "Impossible de charger ce cours.";
		} finally {
			loadingCourse = false;
		}
	}

	function backToList() {
		selectedId = null;
		course = null;
		try {
			sessionStorage.removeItem(LAST_COURSE_KEY);
		} catch {
			// stockage indisponible
		}
	}

	function toggleSection(id: number) {
		const next = new Set(collapsed);
		if (next.has(id)) next.delete(id);
		else next.add(id);
		collapsed = next;
	}

	function saveBlob(blob: Blob, name: string) {
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = name;
		document.body.appendChild(a);
		a.click();
		a.remove();
		setTimeout(() => URL.revokeObjectURL(url), 10000);
	}

	async function download(mod: any, file: any) {
		const key = `${mod.id}-${file.index}`;
		busyFile = key;
		fileError = "";
		try {
			saveBlob(await api.fetchResourceFile(selectedId!, mod.id, file.index), file.name);
		} catch (e: any) {
			fileError = `${file.name} : ${e.message}`;
		} finally {
			busyFile = null;
		}
	}

	async function preview(mod: any, file: any) {
		const key = `${mod.id}-${file.index}`;
		busyFile = key;
		fileError = "";
		// L'onglet doit etre ouvert pendant le clic, sinon le navigateur bloque la fenetre
		const tab = window.open("", "_blank");
		try {
			const blob = await api.fetchResourceFile(selectedId!, mod.id, file.index, true);
			const url = URL.createObjectURL(blob);
			if (tab) tab.location.href = url;
			else saveBlob(blob, file.name);
			setTimeout(() => URL.revokeObjectURL(url), 60000);
		} catch (e: any) {
			tab?.close();
			fileError = `${file.name} : ${e.message}`;
		} finally {
			busyFile = null;
		}
	}

	const PREVIEWABLE = ["application/pdf", "image/png", "image/jpeg", "image/gif", "image/webp"];

	function iconFor(file: any) {
		const n = file.name.toLowerCase();
		const m = file.mime || "";
		if (m.startsWith("image/")) return FileImage;
		if (/\.(zip|rar|7z|tar|gz)$/.test(n)) return FileArchive;
		if (/\.(xlsx?|csv|ods)$/.test(n)) return FileSpreadsheet;
		if (/\.(pptx?|odp)$/.test(n)) return Presentation;
		if (/\.(pkt|py|js|c|cpp|java|json|html|css|sh|ino|cfg|conf|txt)$/.test(n)) return FileCode;
		if (m === "application/pdf" || /\.(docx?|odt|rtf|md)$/.test(n)) return FileText;
		return File;
	}

	function formatSize(bytes: number): string {
		if (!bytes) return "";
		if (bytes < 1024) return `${bytes} o`;
		if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} Ko`;
		return `${(bytes / 1024 / 1024).toFixed(1).replace(".", ",")} Mo`;
	}

	function formatModified(ts: number): string {
		if (!ts) return "";
		return new Date(ts * 1000).toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" });
	}

	function safeLink(url: string | null | undefined): string | null {
		return url && /^https?:\/\//i.test(url) ? url : null;
	}

	const MODULE_LABEL: Record<string, string> = {
		assign: "Devoir",
		quiz: "Quiz",
		forum: "Forum",
		page: "Page",
		folder: "Dossier",
		url: "Lien",
		book: "Livre",
		choice: "Sondage",
		feedback: "Questionnaire",
		wiki: "Wiki",
		glossary: "Glossaire",
		lesson: "Leçon",
		workshop: "Atelier",
		h5pactivity: "Activité H5P",
		scorm: "SCORM",
		bigbluebuttonbn: "Visio",
		zoom: "Visio"
	};

	onMount(() => {
		void loadCourses();
	});
</script>

<div class="space-y-5">
	{#if !configured && !loadingList}
		<Card class="text-center space-y-3 py-10">
			<div class="w-12 h-12 rounded-full bg-app-raised text-muted flex items-center justify-center mx-auto">
				<BookOpen class="w-6 h-6" />
			</div>
			<h2 class="text-base font-bold text-fg">Moodle n'est pas connecté</h2>
			<p class="text-sm text-muted max-w-sm mx-auto">Reliez votre compte Moodle pour retrouver ici vos cours et vos documents, sans passer par le site.</p>
			<button
				type="button"
				onclick={() => onNavigate?.("settings")}
				class="inline-flex items-center rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-semibold px-4 py-2 cursor-pointer"
			>
				Ouvrir les paramètres
			</button>
		</Card>
	{:else}
		<div class="flex flex-col lg:flex-row gap-5 items-start">
			<!-- Liste des cours -->
			<div class="w-full lg:w-72 shrink-0 space-y-3 {selectedId !== null ? 'hidden lg:block' : ''}">
				<div class="flex items-center justify-between">
					<h2 class="text-sm font-bold text-fg">Mes cours</h2>
					<button
						type="button"
						onclick={() => loadCourses(true)}
						disabled={loadingList}
						class="flex items-center gap-1.5 text-xs font-medium text-muted hover:text-fg disabled:opacity-50 cursor-pointer"
						aria-label="Actualiser la liste des cours"
					>
						<RefreshCw class="w-3.5 h-3.5 {loadingList ? 'animate-spin' : ''}" />
						Actualiser
					</button>
				</div>

				<div class="relative">
					<Search class="w-4 h-4 text-subtle absolute left-3 top-2.5" />
					<input
						type="search"
						bind:value={courseQuery}
						aria-label="Rechercher un cours"
						placeholder="Rechercher un cours"
						class="w-full rounded-lg border border-app-border bg-app-surface pl-9 pr-3 py-2 text-sm text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
					/>
				</div>

				{#if listError}
					<p class="text-xs text-red-400 bg-red-600/15 rounded-lg p-3">{listError}</p>
				{/if}

				{#if loadingList && !courses.length}
					<div class="space-y-2">
						{#each Array(5) as _}<Skeleton class="h-14 w-full" />{/each}
					</div>
				{:else if !filteredCourses.length}
					<p class="text-xs text-subtle text-center py-6">{courses.length ? "Aucun cours ne correspond." : "Aucun cours trouvé sur Moodle."}</p>
				{:else}
					<ul class="space-y-1.5">
						{#each filteredCourses as c (c.id)}
							<li>
								<button
									type="button"
									onclick={() => selectCourse(c.id)}
									class="w-full text-left rounded-xl border px-3.5 py-3 transition-colors cursor-pointer {selectedId === c.id ? 'border-cyan-500/60 bg-cyan-600/10' : 'border-app-border bg-app-card hover:bg-app-raised'}"
								>
									<span class="block text-sm font-medium text-fg leading-snug">{c.fullname}</span>
									<span class="flex items-center gap-1.5 mt-1.5">
										{#if c.shortname && c.shortname !== c.fullname}<Badge variant="secondary">{c.shortname}</Badge>{/if}
										{#if c.ended}<Badge variant="secondary">Terminé</Badge>{/if}
									</span>
								</button>
							</li>
						{/each}
					</ul>
				{/if}
			</div>

			<!-- Contenu du cours -->
			<div class="flex-1 min-w-0 w-full {selectedId === null ? 'hidden lg:block' : ''}">
				{#if selectedId === null}
					<Card class="text-center py-16 space-y-2">
						<BookOpen class="w-8 h-8 text-subtle mx-auto" />
						<p class="text-sm text-muted">Choisissez un cours pour voir ses documents.</p>
					</Card>
				{:else}
					<div class="space-y-4">
						<div class="flex items-start justify-between gap-3">
							<div class="min-w-0">
								<button type="button" onclick={backToList} class="lg:hidden flex items-center gap-1 text-xs font-medium text-muted hover:text-fg mb-2 cursor-pointer">
									<ArrowLeft class="w-3.5 h-3.5" /> Mes cours
								</button>
								<h2 class="text-lg font-bold text-fg leading-snug">{selectedCourse?.fullname ?? "Cours"}</h2>
							</div>
							<div class="flex items-center gap-3 shrink-0 pt-1">
								<button
									type="button"
									onclick={() => selectCourse(selectedId!, true)}
									disabled={loadingCourse}
									class="flex items-center gap-1.5 text-xs font-medium text-muted hover:text-fg disabled:opacity-50 cursor-pointer"
									aria-label="Actualiser ce cours"
								>
									<RefreshCw class="w-3.5 h-3.5 {loadingCourse ? 'animate-spin' : ''}" />
									<span class="hidden sm:inline">Actualiser</span>
								</button>
								{#if safeLink(course?.base)}
									<a
										href="{course.base}/course/view.php?id={selectedId}"
										target="_blank"
										rel="noopener noreferrer"
										class="flex items-center gap-1.5 text-xs font-medium text-muted hover:text-fg"
									>
										<ExternalLink class="w-3.5 h-3.5" />
										<span class="hidden sm:inline">Ouvrir sur Moodle</span>
									</a>
								{/if}
							</div>
						</div>

						<div class="relative">
							<Search class="w-4 h-4 text-subtle absolute left-3 top-2.5" />
							<input
								type="search"
								bind:value={query}
								aria-label="Rechercher un document dans ce cours"
								placeholder="Rechercher un document"
								class="w-full rounded-lg border border-app-border bg-app-surface pl-9 pr-3 py-2 text-sm text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none"
							/>
						</div>

						{#if courseError}
							<p class="text-xs text-red-400 bg-red-600/15 rounded-lg p-3">{courseError}</p>
						{/if}
						{#if fileError}
							<p class="text-xs text-red-400 bg-red-600/15 rounded-lg p-3" role="alert">{fileError}</p>
						{/if}

						{#if loadingCourse && !course}
							<div class="space-y-3">
								{#each Array(4) as _}<Skeleton class="h-20 w-full" />{/each}
							</div>
						{:else if course && !visibleSections.length}
							<Card class="text-center py-10">
								<p class="text-sm text-muted">{query ? "Aucun document ne correspond à votre recherche." : "Ce cours ne contient aucune ressource."}</p>
							</Card>
						{:else}
							{#each visibleSections as sec (sec.id)}
								{@const open = !!query.trim() || !collapsed.has(sec.id)}
								<Card class="p-0 overflow-hidden">
									<button
										type="button"
										onclick={() => toggleSection(sec.id)}
										class="w-full flex items-center justify-between gap-3 px-4 py-3 text-left cursor-pointer hover:bg-app-raised/50"
										aria-expanded={open}
									>
										<span class="text-sm font-semibold text-fg">{sec.name}</span>
										<span class="flex items-center gap-2 shrink-0">
											<span class="text-[11px] text-subtle">{sec.modules.length}</span>
											<ChevronDown class="w-4 h-4 text-subtle transition-transform {open ? 'rotate-180' : ''}" />
										</span>
									</button>

									{#if open}
										<div class="border-t border-app-border divide-y divide-app-border">
											{#if sec.summary && !query.trim()}
												<p class="px-4 py-3 text-xs text-muted leading-relaxed">{sec.summary}</p>
											{/if}
											{#each sec.modules as mod (mod.id)}
												<div class="px-4 py-3 space-y-2">
													{#if mod.files.length === 1 && mod.modname === "resource"}
														<!-- Document unique : une seule ligne -->
														{@const f = mod.files[0]}
														{@const Icon = iconFor(f)}
														<div class="flex items-center gap-3">
															<Icon class="w-5 h-5 text-muted shrink-0" />
															<div class="min-w-0 flex-1">
																<p class="text-sm text-fg truncate" title={mod.name}>{mod.name}</p>
																<p class="text-[11px] text-subtle truncate">{[f.name !== mod.name ? f.name : "", formatSize(f.size), formatModified(f.modified)].filter(Boolean).join(" · ")}</p>
															</div>
															{@render fileActions(mod, f)}
														</div>
													{:else if mod.files.length}
														<!-- Dossier ou activite avec plusieurs fichiers -->
														<div class="flex items-center gap-3">
															<Folder class="w-5 h-5 text-muted shrink-0" />
															<p class="text-sm font-medium text-fg min-w-0 truncate" title={mod.name}>{mod.name}</p>
														</div>
														<ul class="ml-8 space-y-1.5">
															{#each mod.files as f (f.index)}
																{@const Icon = iconFor(f)}
																<li class="flex items-center gap-3">
																	<Icon class="w-4 h-4 text-subtle shrink-0" />
																	<div class="min-w-0 flex-1">
																		<p class="text-sm text-fg truncate" title={f.name}>{f.name}</p>
																		<p class="text-[11px] text-subtle">{[formatSize(f.size), formatModified(f.modified)].filter(Boolean).join(" · ")}</p>
																	</div>
																	{@render fileActions(mod, f)}
																</li>
															{/each}
														</ul>
													{:else if mod.link}
														<div class="flex items-center gap-3">
															<Link2 class="w-5 h-5 text-muted shrink-0" />
															<p class="text-sm text-fg min-w-0 flex-1 truncate" title={mod.name}>{mod.name}</p>
															{#if safeLink(mod.link)}
																<a href={mod.link} target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-xs font-medium text-muted hover:text-fg shrink-0">
																	Ouvrir <ExternalLink class="w-3.5 h-3.5" />
																</a>
															{/if}
														</div>
													{:else}
														<!-- Activite (devoir, quiz, forum...) ou texte : consultable sur Moodle -->
														<div class="flex items-center gap-3">
															<BookOpen class="w-5 h-5 text-muted shrink-0" />
															<div class="min-w-0 flex-1">
																<p class="text-sm text-fg truncate" title={mod.name}>{mod.name}</p>
															</div>
															{#if MODULE_LABEL[mod.modname]}<Badge variant="secondary">{MODULE_LABEL[mod.modname]}</Badge>{/if}
															{#if safeLink(mod.url) && mod.modname !== "label"}
																<a href={mod.url} target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-xs font-medium text-muted hover:text-fg shrink-0">
																	Moodle <ExternalLink class="w-3.5 h-3.5" />
																</a>
															{/if}
														</div>
													{/if}

													{#if mod.description}
														<p class="text-xs text-muted leading-relaxed ml-8 line-clamp-3">{mod.description}</p>
													{/if}
												</div>
											{/each}
										</div>
									{/if}
								</Card>
							{/each}
						{/if}
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

{#snippet fileActions(mod: any, f: any)}
	<div class="flex items-center gap-1 shrink-0">
		{#if PREVIEWABLE.includes(f.mime)}
			<button
				type="button"
				onclick={() => preview(mod, f)}
				disabled={busyFile === `${mod.id}-${f.index}`}
				class="p-2 rounded-lg text-muted hover:text-fg hover:bg-app-raised disabled:opacity-50 cursor-pointer"
				aria-label="Aperçu de {f.name}"
				title="Aperçu"
			>
				<Eye class="w-4 h-4" />
			</button>
		{/if}
		<button
			type="button"
			onclick={() => download(mod, f)}
			disabled={busyFile === `${mod.id}-${f.index}`}
			class="p-2 rounded-lg text-muted hover:text-fg hover:bg-app-raised disabled:opacity-50 cursor-pointer"
			aria-label="Télécharger {f.name}"
			title="Télécharger"
		>
			<Download class="w-4 h-4 {busyFile === `${mod.id}-${f.index}` ? 'animate-pulse' : ''}" />
		</button>
	</div>
{/snippet}
