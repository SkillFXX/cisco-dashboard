<script lang="ts">
	import { onMount } from "svelte";
	import { cn } from "$lib/utils";
	import { api } from "$lib/api";
	import { auth } from "$lib/stores/auth.svelte";
	import Button from "./Button.svelte";
	import Badge from "./Badge.svelte";
	import {
		X,
		FileText,
		BookOpen,
		Calendar,
		Check,
		ArrowRight,
		ArrowLeft,
		Link2,
		AlertCircle
	} from "lucide-svelte";

	let {
		open = $bindable(false),
		onComplete
	}: {
		open: boolean;
		onComplete?: () => void;
	} = $props();

	let currentStep = $state(1); // 1: ScoDoc, 2: Moodle, 3: Emploi du temps, 4: Recap

	// ScoDoc state
	let scodoc_url = $state("");
	let scodoc_username = $state("");
	let scodoc_password = $state("");
	let scodocSaved = $state(false);

	// Moodle state
	let moodle_url = $state("");
	let moodle_username = $state("");
	let moodle_password = $state("");
	let moodle_token = $state("");
	let moodleSaved = $state(false);

	// Emploi du temps
	let ical_url = $state("");
	let icalSaved = $state(false);

	const fieldClass = "w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-sm text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none";
	const steps = ["ScoDoc", "Moodle", "Emploi du temps"];

	let isSaving = $state(false);
	let stepError = $state("");

	// Load existing settings if any
	onMount(async () => {
		try {
			const data = await api.getSettings();
			if (data.scodoc_url) scodoc_url = data.scodoc_url;
			if (data.scodoc_username) {
				scodoc_username = data.scodoc_username;
				scodocSaved = data.scodoc_configured;
			}
			if (data.moodle_url) moodle_url = data.moodle_url;
			if (data.moodle_username) {
				moodle_username = data.moodle_username;
				moodleSaved = data.moodle_configured;
			}
			if (data.ical_url) {
				ical_url = data.ical_url;
				icalSaved = data.ical_configured;
			}
		} catch {
			// ignore on initial load
		}
	});

	function handleClose() {
		if (typeof window !== "undefined") {
			localStorage.setItem("cisco_onboarding_done", "true");
		}
		open = false;
		onComplete?.();
	}

	async function saveStepScoDoc() {
		if (!scodoc_username.trim() || !scodoc_password.trim()) {
			stepError = "Renseignez votre identifiant et votre mot de passe, ou passez cette étape.";
			return;
		}

		isSaving = true;
		stepError = "";
		try {
			const res = await api.verifyService({
				service: "scodoc",
				url: scodoc_url.trim(),
				username: scodoc_username.trim(),
				password: scodoc_password.trim(),
				save_if_valid: true
			});

			if (!res.success) {
				stepError = res.message || "Identifiant CAS ENT ou mot de passe ScoDoc incorrect.";
				scodocSaved = false;
				return;
			}

			scodocSaved = true;
			if (res.student_name && auth.user) {
				auth.user.full_name = res.student_name;
			}
			if (res.student_pic && auth.user) {
				auth.user.photo_base64 = res.student_pic;
			}
			currentStep = 2;
		} catch (e: any) {
			stepError = e.message || "Erreur lors de la vérification ScoDoc.";
			scodocSaved = false;
		} finally {
			isSaving = false;
		}
	}

	async function saveStepMoodle() {
		if (!moodle_token.trim() && (!moodle_username.trim() || !moodle_password.trim())) {
			stepError = "Renseignez votre identifiant et votre mot de passe Moodle, ou passez cette étape.";
			return;
		}

		isSaving = true;
		stepError = "";
		try {
			const res = await api.verifyService({
				service: "moodle",
				url: moodle_url.trim(),
				username: moodle_username.trim() || undefined,
				password: moodle_password.trim() || undefined,
				token: moodle_token.trim() || undefined,
				save_if_valid: true
			});

			if (!res.success) {
				stepError = res.message || "Identifiant ou mot de passe Moodle incorrect.";
				moodleSaved = false;
				return;
			}

			moodleSaved = true;
			if (res.url) moodle_url = res.url;
			if (res.student_name && auth.user && !auth.user.full_name) {
				auth.user.full_name = res.student_name;
			}
			currentStep = 3;
		} catch (e: any) {
			stepError = e.message || "Erreur lors de la vérification Moodle.";
			moodleSaved = false;
		} finally {
			isSaving = false;
		}
	}

	async function saveStepIcal() {
		if (!ical_url.trim()) {
			stepError = "Collez le lien de votre emploi du temps, ou passez cette étape.";
			return;
		}

		isSaving = true;
		stepError = "";
		try {
			const res = await api.verifyService({
				service: "ical",
				url: ical_url.trim(),
				save_if_valid: true
			});

			if (!res.success) {
				stepError = res.message || "Lien iCal invalide ou inaccessible.";
				icalSaved = false;
				return;
			}

			icalSaved = true;
			currentStep = 4;
		} catch (e: any) {
			stepError = e.message || "Erreur lors de l'enregistrement de l'emploi du temps.";
			icalSaved = false;
		} finally {
			isSaving = false;
		}
	}

	function finishOnboarding() {
		handleClose();
	}
</script>

{#snippet stepHead(Icon: any, title: string, purpose: string)}
	<div class="flex items-center gap-3">
		<div class="w-10 h-10 rounded-xl bg-app-raised text-muted flex items-center justify-center shrink-0">
			<Icon class="w-5 h-5" />
		</div>
		<div>
			<h3 class="font-bold text-fg text-base leading-tight">{title}</h3>
			<p class="text-xs text-muted mt-0.5">{purpose}</p>
		</div>
	</div>
{/snippet}

{#snippet footer(back: number | null, skipTo: number, label: string, action: () => void)}
	<div class="flex items-center justify-between gap-3 pt-5 border-t border-app-border">
		{#if back}
			<button type="button" onclick={() => { stepError = ""; currentStep = back; }} class="flex items-center gap-1 text-xs font-medium text-muted hover:text-fg cursor-pointer">
				<ArrowLeft class="w-3.5 h-3.5" /> Précédent
			</button>
		{:else}
			<span></span>
		{/if}
		<div class="flex items-center gap-4">
			<button type="button" onclick={() => { stepError = ""; currentStep = skipTo; }} class="text-xs font-medium text-muted hover:text-fg cursor-pointer">
				Passer
			</button>
			<Button variant="cisco" onclick={action} disabled={isSaving}>
				{isSaving ? "Vérification..." : label}
				<ArrowRight class="w-4 h-4 ml-1" />
			</Button>
		</div>
	</div>
{/snippet}

{#if open}
	<div class="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs" onclick={handleClose} role="presentation"></div>

	<div class="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto">
		<div class="relative w-full max-w-xl rounded-2xl border border-app-border bg-app-card p-6 sm:p-8 text-fg shadow-2xl my-8" role="dialog" aria-modal="true" aria-label="Assistant de configuration">
			<button onclick={handleClose} class="absolute right-5 top-5 rounded-lg p-1.5 text-muted hover:bg-app-raised hover:text-fg cursor-pointer" aria-label="Fermer">
				<X class="w-5 h-5" />
			</button>

			<div class="pr-8 mb-6">
				<h2 class="text-xl font-bold text-fg tracking-tight">Bienvenue, reliez vos services</h2>
				<p class="text-sm text-muted mt-1">Trois étapes, toutes facultatives. Vous pourrez tout modifier plus tard dans les Paramètres.</p>
			</div>

			<!-- Progression -->
			<div class="mb-6">
				<div class="grid grid-cols-3 gap-1.5">
					{#each steps as name, i}
						<div class="h-1.5 rounded-full {currentStep > i + 1 || currentStep === 4 ? 'bg-cyan-600' : currentStep === i + 1 ? 'bg-cyan-500/60' : 'bg-app-raised'}"></div>
					{/each}
				</div>
				<p class="text-xs text-muted mt-2">
					{#if currentStep < 4}Étape {currentStep} sur 3 · <span class="text-fg font-medium">{steps[currentStep - 1]}</span>{:else}Récapitulatif{/if}
				</p>
			</div>

			{#if stepError}
				<div class="p-3 mb-5 rounded-lg bg-red-600/15 text-red-400 text-xs font-medium flex items-start gap-2" role="alert">
					<AlertCircle class="w-4 h-4 shrink-0 mt-px" />
					<span>{stepError}</span>
				</div>
			{/if}

			{#if currentStep === 1}
				<div class="space-y-5">
					{@render stepHead(FileText, "ScoDoc", "Vos notes, moyennes, rang et absences.")}

					<div class="space-y-3">
						<div>
							<label for="onb-sco-url" class="block text-xs font-medium text-fg mb-1">Adresse de ScoDoc</label>
							<input id="onb-sco-url" type="text" bind:value={scodoc_url} placeholder="https://scodoc.votre-iut.fr" class={fieldClass} />
							<p class="text-[11px] text-subtle mt-1">L'adresse du site où vous consultez vos notes.</p>
						</div>
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
							<div>
								<label for="onb-sco-u" class="block text-xs font-medium text-fg mb-1">Identifiant</label>
								<input id="onb-sco-u" type="text" bind:value={scodoc_username} autocomplete="off" placeholder="prenom.nom" class={fieldClass} />
							</div>
							<div>
								<label for="onb-sco-p" class="block text-xs font-medium text-fg mb-1">Mot de passe</label>
								<input id="onb-sco-p" type="password" bind:value={scodoc_password} autocomplete="off" placeholder="••••••••" class={fieldClass} />
							</div>
						</div>
					</div>

					<details class="group rounded-lg border border-app-border bg-app-surface px-3 py-2.5 text-xs text-muted">
						<summary class="cursor-pointer font-medium text-fg list-none flex items-center justify-between">
							Quel identifiant utiliser ?
							<span class="text-subtle group-open:rotate-180 transition-transform">▾</span>
						</summary>
						<p class="mt-2 leading-relaxed">
							Ceux de votre compte université / ENT, les mêmes que pour vous connecter à ScoDoc. Ils sont chiffrés sur le serveur et servent uniquement à récupérer vos notes et absences.
						</p>
					</details>

					{@render footer(null, 2, "Connecter ScoDoc", saveStepScoDoc)}
				</div>

			{:else if currentStep === 2}
				<div class="space-y-5">
					{@render stepHead(BookOpen, "Moodle", "Vos cours et devoirs à rendre.")}

					<div class="space-y-3">
						<div>
							<label for="onb-mdl-url" class="block text-xs font-medium text-fg mb-1">Adresse de Moodle</label>
							<input id="onb-mdl-url" type="text" bind:value={moodle_url} placeholder="https://moodle.votre-iut.fr" class={fieldClass} />
							<p class="text-[11px] text-subtle mt-1">L'adresse du Moodle de votre IUT. Inutile d'ajouter « /moodle » : il est détecté automatiquement.</p>
						</div>
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
							<div>
								<label for="onb-mdl-u" class="block text-xs font-medium text-fg mb-1">Identifiant</label>
								<input id="onb-mdl-u" type="text" bind:value={moodle_username} autocomplete="off" placeholder="prenom.nom" class={fieldClass} />
							</div>
							<div>
								<label for="onb-mdl-p" class="block text-xs font-medium text-fg mb-1">Mot de passe</label>
								<input id="onb-mdl-p" type="password" bind:value={moodle_password} autocomplete="off" placeholder="••••••••" class={fieldClass} />
							</div>
						</div>
					</div>

					<details class="group rounded-lg border border-app-border bg-app-surface px-3 py-2.5 text-xs text-muted">
						<summary class="cursor-pointer font-medium text-fg list-none flex items-center justify-between">
							La connexion échoue ? Utiliser un jeton
							<span class="text-subtle group-open:rotate-180 transition-transform">▾</span>
						</summary>
						<div class="mt-2 space-y-2 leading-relaxed">
							<p>Si votre Moodle refuse le mot de passe, vous pouvez coller à la place un jeton personnel : Moodle › Préférences › Clés de sécurité › « Moodle mobile web service ».</p>
							<input id="onb-mdl-token" type="text" bind:value={moodle_token} aria-label="Jeton Moodle" placeholder="Jeton personnel" class={fieldClass} />
						</div>
					</details>

					{@render footer(1, 3, "Connecter Moodle", saveStepMoodle)}
				</div>

			{:else if currentStep === 3}
				<div class="space-y-5">
					{@render stepHead(Calendar, "Emploi du temps", "Vos cours, salles, enseignants et évaluations à venir.")}

					<div>
						<label for="onb-ical" class="block text-xs font-medium text-fg mb-1">Lien de votre emploi du temps</label>
						<div class="flex items-center gap-2">
							<Link2 class="w-4 h-4 text-subtle shrink-0" />
							<input id="onb-ical" type="url" bind:value={ical_url} placeholder="https://.../export.ics" class={fieldClass} />
						</div>
					</div>

					<details class="group rounded-lg border border-app-border bg-app-surface px-3 py-2.5 text-xs text-muted" open>
						<summary class="cursor-pointer font-medium text-fg list-none flex items-center justify-between">
							Où trouver ce lien ?
							<span class="text-subtle group-open:rotate-180 transition-transform">▾</span>
						</summary>
						<ol class="mt-2 space-y-1 leading-relaxed list-decimal pl-4">
							<li>Ouvrez le site où vous consultez votre emploi du temps.</li>
							<li>Cherchez une option d'<strong class="text-fg">export</strong> ou d'<strong class="text-fg">abonnement</strong> au calendrier, nommée « iCal », « .ics » ou « Exporter ».</li>
							<li>Copiez le lien proposé et collez-le ci-dessus.</li>
						</ol>
					</details>

					{@render footer(2, 4, "Enregistrer", saveStepIcal)}
				</div>

			{:else}
				<div class="space-y-5">
					<div class="text-center space-y-2">
						<div class="w-12 h-12 rounded-full bg-emerald-600/15 text-emerald-400 flex items-center justify-center mx-auto">
							<Check class="w-6 h-6" />
						</div>
						<h3 class="font-bold text-fg text-base">
							{#if scodocSaved && moodleSaved && icalSaved}Tout est connecté{:else if scodocSaved || moodleSaved || icalSaved}Configuration partielle{:else}Aucun service relié{/if}
						</h3>
						<p class="text-xs text-muted max-w-sm mx-auto">
							{#if scodocSaved && moodleSaved && icalSaved}
								Vos données vont se synchroniser automatiquement.
							{:else}
								Un service non relié n'affichera pas de données. Vous pouvez le connecter à tout moment dans les Paramètres.
							{/if}
						</p>
					</div>

					<ul class="divide-y divide-app-border rounded-xl border border-app-border bg-app-surface">
						{#each [{ name: "ScoDoc", Icon: FileText, ok: scodocSaved }, { name: "Moodle", Icon: BookOpen, ok: moodleSaved }, { name: "Emploi du temps", Icon: Calendar, ok: icalSaved }] as row}
							<li class="flex items-center justify-between px-4 py-3">
								<span class="flex items-center gap-2 text-sm text-fg"><row.Icon class="w-4 h-4 text-muted" /> {row.name}</span>
								<Badge variant={row.ok ? "success" : "secondary"}>{row.ok ? "Connecté" : "Non relié"}</Badge>
							</li>
						{/each}
					</ul>

					<Button variant="cisco" class="w-full" onclick={finishOnboarding}>
						Accéder à mon tableau de bord
						<ArrowRight class="w-4 h-4 ml-1" />
					</Button>
				</div>
			{/if}
		</div>
	</div>
{/if}
