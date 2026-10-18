<script lang="ts">
	import { onMount } from "svelte";
	import { cn } from "$lib/utils";
	import { api } from "$lib/api";
	import { auth } from "$lib/stores/auth.svelte";
	import Button from "./Button.svelte";
	import {
		X,
		FileText,
		BookOpen,
		Calendar,
		Check,
		ArrowRight,
		ArrowLeft,
		Sparkles,
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

	let currentStep = $state(1); // 1: ScoDoc, 2: Moodle, 3: ADE, 4: Recap

	// ScoDoc state
	let scodoc_url = $state("https://wscodoc.iutbeziers.fr");
	let scodoc_username = $state("");
	let scodoc_password = $state("");
	let scodocSaved = $state(false);

	// Moodle state
	let moodle_url = $state("https://moodle-but.iutbeziers.fr/moodle");
	let moodle_username = $state("");
	let moodle_password = $state("");
	let moodle_token = $state("");
	let moodleSaved = $state(false);

	// ADE state
	let ical_url = $state("");
	let icalSaved = $state(false);

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
			stepError = "Veuillez renseigner votre identifiant et votre mot de passe CAS, ou cliquez sur 'Passer cette étape'.";
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
			stepError = "Veuillez renseigner vos identifiants Moodle ou votre jeton, ou cliquez sur 'Passer cette étape'.";
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
			stepError = "Veuillez coller le lien de votre flux iCal (.ics) ou cliquez sur 'Passer cette étape'.";
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

{#if open}
	<!-- Backdrop -->
	<div
		class="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs transition-opacity animate-in fade-in duration-200"
		onclick={handleClose}
		role="presentation"
	></div>

	<!-- Modal Container -->
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto">
		<div
			class="relative w-full max-w-2xl rounded-2xl border border-app-border bg-app-card p-6 sm:p-8 text-zinc-100 shadow-2xl animate-in zoom-in-95 duration-200 my-8"
			role="dialog"
			aria-modal="true"
		>
			<!-- Close button -->
			<button
				onclick={handleClose}
				class="absolute right-5 top-5 rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-white transition-colors cursor-pointer"
				aria-label="Fermer"
			>
				<X class="w-5 h-5" />
			</button>

			<!-- Header -->
			<div class="space-y-1 pr-8 mb-6">
				<div class="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-cyan-600 text-white text-xs font-semibold mb-2">
					<Sparkles class="w-3.5 h-3.5" />
					<span>Assistant d'intégration</span>
				</div>
				<h2 class="text-xl sm:text-2xl font-black text-white tracking-tight">
					Configuration de vos Services
				</h2>
				<p class="text-xs text-zinc-400">
					Reliez vos services universitaires un par un pour synchroniser automatiquement vos notes, devoirs et emploi du temps.
				</p>
			</div>

			<!-- Stepper Navigation -->
			<div class="grid grid-cols-4 gap-2 mb-6 pb-4 border-b border-app-border">
				<!-- Step 1 -->
				<div class="flex items-center gap-2 text-xs">
					<div class="w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs shrink-0 {currentStep === 1 ? 'bg-cyan-600 text-white' : scodocSaved ? 'bg-emerald-600 text-white' : 'bg-zinc-800 text-zinc-400'}">
						{#if scodocSaved}
							<Check class="w-3.5 h-3.5" />
						{:else}
							<span>1</span>
						{/if}
					</div>
					<span class="hidden sm:inline font-medium text-xs {currentStep === 1 ? 'text-white' : 'text-zinc-500'}">ScoDoc</span>
				</div>

				<!-- Step 2 -->
				<div class="flex items-center gap-2 text-xs">
					<div class="w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs shrink-0 {currentStep === 2 ? 'bg-cyan-600 text-white' : moodleSaved ? 'bg-emerald-600 text-white' : 'bg-zinc-800 text-zinc-400'}">
						{#if moodleSaved}
							<Check class="w-3.5 h-3.5" />
						{:else}
							<span>2</span>
						{/if}
					</div>
					<span class="hidden sm:inline font-medium text-xs {currentStep === 2 ? 'text-white' : 'text-zinc-500'}">Moodle</span>
				</div>

				<!-- Step 3 -->
				<div class="flex items-center gap-2 text-xs">
					<div class="w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs shrink-0 {currentStep === 3 ? 'bg-cyan-600 text-white' : icalSaved ? 'bg-emerald-600 text-white' : 'bg-zinc-800 text-zinc-400'}">
						{#if icalSaved}
							<Check class="w-3.5 h-3.5" />
						{:else}
							<span>3</span>
						{/if}
					</div>
					<span class="hidden sm:inline font-medium text-xs {currentStep === 3 ? 'text-white' : 'text-zinc-500'}">ADE Planning</span>
				</div>

				<!-- Step 4 -->
				<div class="flex items-center gap-2 text-xs">
					<div class="w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs shrink-0 {currentStep === 4 ? 'bg-cyan-600 text-white' : 'bg-zinc-800 text-zinc-400'}">
						<span>4</span>
					</div>
					<span class="hidden sm:inline font-medium text-xs {currentStep === 4 ? 'text-white' : 'text-zinc-500'}">Prêt</span>
				</div>
			</div>

			<!-- Error message if any -->
			{#if stepError}
				<div class="p-3 mb-5 rounded-lg bg-red-600/20 text-red-300 text-xs font-medium flex items-center gap-2">
					<AlertCircle class="w-4 h-4 shrink-0" />
					<span>{stepError}</span>
				</div>
			{/if}

			<!-- Step 1 : ScoDoc -->
			{#if currentStep === 1}
				<div class="space-y-4">
					<div class="flex items-center gap-3 p-3.5 rounded-xl bg-emerald-600/10 border border-emerald-500/20">
						<div class="w-10 h-10 rounded-xl bg-emerald-600/20 text-emerald-400 flex items-center justify-center shrink-0">
							<FileText class="w-5 h-5" />
						</div>
						<div>
							<h3 class="font-bold text-white text-sm">Étape 1 : Relevé ScoDoc (Notes & Absences)</h3>
							<p class="text-xs text-zinc-400 mt-0.5">
								Importe vos moyennes par UE, classement, et absences. Votre nom et photo d'étudiant sont synchronisés automatiquement.
							</p>
						</div>
					</div>

					<div class="space-y-3 pt-2">
						<div>
							<label for="onb-sco-url" class="block text-xs font-medium text-zinc-400 mb-1">URL du serveur ScoDoc</label>
							<input
								id="onb-sco-url"
								type="text"
								bind:value={scodoc_url}
								placeholder="https://wscodoc.iutbeziers.fr"
								class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
							/>
						</div>
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
							<div>
								<label for="onb-sco-u" class="block text-xs font-medium text-zinc-400 mb-1">Identifiant CAS ENT</label>
								<input
									id="onb-sco-u"
									type="text"
									bind:value={scodoc_username}
									placeholder="ex: prenom.nom"
									class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
								/>
							</div>
							<div>
								<label for="onb-sco-p" class="block text-xs font-medium text-zinc-400 mb-1">Mot de passe CAS ENT</label>
								<input
									id="onb-sco-p"
									type="password"
									bind:value={scodoc_password}
									placeholder="••••••••••••"
									class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
								/>
							</div>
						</div>
					</div>

					<div class="flex items-center justify-between pt-5 border-t border-app-border">
						<button
							type="button"
							onclick={() => { stepError = ""; currentStep = 2; }}
							class="text-xs font-medium text-zinc-400 hover:text-white transition-colors cursor-pointer"
						>
							Passer cette étape
						</button>
						<Button variant="cisco" onclick={saveStepScoDoc} disabled={isSaving}>
							{isSaving ? "Vérification en cours..." : "Vérifier & Connecter ScoDoc"}
							<ArrowRight class="w-4 h-4 ml-1" />
						</Button>
					</div>
				</div>

			<!-- Step 2 : Moodle -->
			{:else if currentStep === 2}
				<div class="space-y-4">
					<div class="flex items-center gap-3 p-3.5 rounded-xl bg-amber-600/10 border border-amber-500/20">
						<div class="w-10 h-10 rounded-xl bg-amber-600/20 text-amber-400 flex items-center justify-center shrink-0">
							<BookOpen class="w-5 h-5" />
						</div>
						<div>
							<h3 class="font-bold text-white text-sm">Étape 2 : Moodle (Devoirs & DM)</h3>
							<p class="text-xs text-zinc-400 mt-0.5">
								Récupère les dates d'échéances de vos devoirs à rendre, devoirs maison et travaux pratiques.
							</p>
						</div>
					</div>

					<div class="space-y-3 pt-2">
						<div>
							<label for="onb-mdl-url" class="block text-xs font-medium text-zinc-400 mb-1">URL de votre Moodle</label>
							<input
								id="onb-mdl-url"
								type="text"
								bind:value={moodle_url}
								placeholder="https://moodle-but.iutbeziers.fr/moodle"
								class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
							/>
						</div>
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
							<div>
								<label for="onb-mdl-u" class="block text-xs font-medium text-zinc-400 mb-1">Identifiant Moodle</label>
								<input
									id="onb-mdl-u"
									type="text"
									bind:value={moodle_username}
									placeholder="ex: prenom.nom"
									class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
								/>
							</div>
							<div>
								<label for="onb-mdl-p" class="block text-xs font-medium text-zinc-400 mb-1">Mot de passe Moodle</label>
								<input
									id="onb-mdl-p"
									type="password"
									bind:value={moodle_password}
									placeholder="••••••••••••"
									class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
								/>
							</div>
						</div>
						<div>
							<label for="onb-mdl-token" class="block text-xs font-medium text-zinc-400 mb-1">Ou Jeton WebService Moodle (optionnel)</label>
							<input
								id="onb-mdl-token"
								type="text"
								bind:value={moodle_token}
								placeholder="Ex: 8f9b4c2e1a3d5e7f9a0b1c2d3e4f5a6b"
								class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
							/>
						</div>
					</div>

					<div class="flex items-center justify-between pt-5 border-t border-app-border">
						<button
							type="button"
							onclick={() => { stepError = ""; currentStep = 1; }}
							class="flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-white transition-colors cursor-pointer"
						>
							<ArrowLeft class="w-3.5 h-3.5" />
							<span>Précédent</span>
						</button>
						<div class="flex items-center gap-3">
							<button
								type="button"
								onclick={() => { stepError = ""; currentStep = 3; }}
								class="text-xs font-medium text-zinc-400 hover:text-white transition-colors cursor-pointer"
							>
								Passer cette étape
							</button>
							<Button variant="cisco" onclick={saveStepMoodle} disabled={isSaving}>
								{isSaving ? "Vérification en cours..." : "Vérifier & Connecter Moodle"}
								<ArrowRight class="w-4 h-4 ml-1" />
							</Button>
						</div>
					</div>
				</div>

			<!-- Step 3 : ADE Campus iCal -->
			{:else if currentStep === 3}
				<div class="space-y-4">
					<div class="flex items-center gap-3 p-3.5 rounded-xl bg-blue-600/10 border border-blue-500/20">
						<div class="w-10 h-10 rounded-xl bg-blue-600/20 text-blue-400 flex items-center justify-center shrink-0">
							<Calendar class="w-5 h-5" />
						</div>
						<div>
							<h3 class="font-bold text-white text-sm">Étape 3 : Emploi du Temps ADE Campus</h3>
							<p class="text-xs text-zinc-400 mt-0.5">
								Affiche en direct vos cours, salles, professeurs et créneaux de devoirs surveillés (DS).
							</p>
						</div>
					</div>

					<div class="space-y-3 pt-2">
						<div>
							<label for="onb-ical" class="block text-xs font-medium text-zinc-400 mb-1">Lien de l'URL exportée (.ics)</label>
							<div class="flex items-center gap-2">
								<Link2 class="w-4 h-4 text-zinc-500 shrink-0" />
								<input
									id="onb-ical"
									type="url"
									bind:value={ical_url}
									placeholder="https://edt.umontpellier.fr/.../export.ics"
									class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none"
								/>
							</div>
						</div>
						<div class="p-3 rounded-lg bg-zinc-900 border border-app-border text-[11px] text-zinc-400 leading-relaxed">
							<strong>Où trouver ce lien ?</strong> Connectez-vous sur votre ENT ou ADE Campus, ouvrez votre planning, cliquez sur <em>Options d'exportation</em> ou <em>S'abonner</em>, puis copiez l'adresse web du lien iCal (.ics).
						</div>
					</div>

					<div class="flex items-center justify-between pt-5 border-t border-app-border">
						<button
							type="button"
							onclick={() => { stepError = ""; currentStep = 2; }}
							class="flex items-center gap-1 text-xs font-medium text-zinc-400 hover:text-white transition-colors cursor-pointer"
						>
							<ArrowLeft class="w-3.5 h-3.5" />
							<span>Précédent</span>
						</button>
						<div class="flex items-center gap-3">
							<button
								type="button"
								onclick={() => { stepError = ""; currentStep = 4; }}
								class="text-xs font-medium text-zinc-400 hover:text-white transition-colors cursor-pointer"
							>
								Passer cette étape
							</button>
							<Button variant="cisco" onclick={saveStepIcal} disabled={isSaving}>
								{isSaving ? "Vérification du flux..." : "Vérifier & Enregistrer ADE"}
								<ArrowRight class="w-4 h-4 ml-1" />
							</Button>
						</div>
					</div>
				</div>

			<!-- Step 4 : Recap & Finalisation -->
			{:else}
				<div class="space-y-5">
					<div class="text-center py-2 space-y-2">
						<div class="w-12 h-12 rounded-full bg-emerald-600/20 text-emerald-400 flex items-center justify-center mx-auto">
							<Check class="w-6 h-6" />
						</div>
						<h3 class="font-bold text-white text-base">Configuration Terminée !</h3>
						<p class="text-xs text-zinc-400 max-w-md mx-auto">
							Votre espace de travail Cisco Student est configuré. Voici le récapitulatif de vos connexions :
						</p>
					</div>

					<!-- Recap Tiles -->
					<div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
						<!-- ScoDoc -->
						<div class="p-4 rounded-xl border border-app-border bg-app-surface flex flex-col justify-between space-y-3">
							<div class="flex items-center gap-2">
								<FileText class="w-4 h-4 text-emerald-400" />
								<span class="text-xs font-bold text-white">ScoDoc</span>
							</div>
							<div>
								{#if scodocSaved}
									<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-emerald-600 text-white">
										Vérifié & Connecté
									</span>
								{:else}
									<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-zinc-700 text-white">
										Non relié
									</span>
								{/if}
							</div>
						</div>

						<!-- Moodle -->
						<div class="p-4 rounded-xl border border-app-border bg-app-surface flex flex-col justify-between space-y-3">
							<div class="flex items-center gap-2">
								<BookOpen class="w-4 h-4 text-amber-400" />
								<span class="text-xs font-bold text-white">Moodle</span>
							</div>
							<div>
								{#if moodleSaved}
									<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-emerald-600 text-white">
										Vérifié & Connecté
									</span>
								{:else}
									<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-zinc-700 text-white">
										Non relié
									</span>
								{/if}
							</div>
						</div>

						<!-- ADE Campus -->
						<div class="p-4 rounded-xl border border-app-border bg-app-surface flex flex-col justify-between space-y-3">
							<div class="flex items-center gap-2">
								<Calendar class="w-4 h-4 text-blue-400" />
								<span class="text-xs font-bold text-white">ADE Campus</span>
							</div>
							<div>
								{#if icalSaved}
									<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-emerald-600 text-white">
										Vérifié & Connecté
									</span>
								{:else}
									<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold bg-zinc-700 text-white">
										Non relié
									</span>
								{/if}
							</div>
						</div>
					</div>

					{#if auth.user?.full_name}
						<div class="p-3.5 rounded-xl border border-cyan-500/30 bg-cyan-950/20 flex items-center justify-between">
							<div class="flex items-center gap-2">
								<Sparkles class="w-4 h-4 text-cyan-400" />
								<span class="text-xs text-zinc-300">Identité étudiante confirmée :</span>
							</div>
							<span class="text-xs font-bold text-white">{auth.user.full_name}</span>
						</div>
					{/if}

					<p class="text-[11px] text-zinc-400 text-center">
						Toutes ces connexions restent modifiables à tout moment dans l'onglet <strong>Paramètres</strong>.
					</p>

					<div class="pt-3 border-t border-app-border">
						<Button variant="cisco" class="w-full" onclick={finishOnboarding}>
							Accéder à mon tableau de bord
							<ArrowRight class="w-4 h-4 ml-1" />
						</Button>
					</div>
				</div>
			{/if}
		</div>
	</div>
{/if}
