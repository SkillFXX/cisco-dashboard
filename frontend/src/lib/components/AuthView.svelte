<script lang="ts">
	import { auth } from "$lib/stores/auth.svelte";
	import Card from "./Card.svelte";
	import Button from "./Button.svelte";
	import Badge from "./Badge.svelte";
	import { ArrowRight, User, Lock } from "lucide-svelte";

	let mode = $state<"login" | "register">("login");

	// Login state
	let loginUsername = $state("");
	let loginPassword = $state("");

	// Register state
	let regUsername = $state("");
	let regEmail = $state("");
	let regPassword = $state("");
	let regFullName = $state("");

	// Integrated platforms during signup
	let scodocUrl = $state("https://wscodoc.iutbeziers.fr");
	let scodocUser = $state("");
	let scodocPass = $state("");

	let moodleUrl = $state("https://moodle.umontpellier.fr");
	let moodleUser = $state("");
	let moodlePass = $state("");

	let icalUrl = $state("");

	let isSubmitting = $state(false);
	let error = $state("");

	async function handleLogin(e: SubmitEvent) {
		e.preventDefault();
		isSubmitting = true;
		error = "";
		try {
			await auth.login(loginUsername, loginPassword);
		} catch (err: any) {
			error = err.message || "Identifiants invalides";
		} finally {
			isSubmitting = false;
		}
	}

	async function handleRegister(e: SubmitEvent) {
		e.preventDefault();
		isSubmitting = true;
		error = "";
		try {
			await auth.register({
				username: regUsername,
				email: regEmail,
				password: regPassword,
				full_name: regFullName,
				scodoc_url: scodocUrl,
				scodoc_username: scodocUser || undefined,
				scodoc_password: scodocPass || undefined,
				moodle_url: moodleUrl,
				moodle_username: moodleUser || undefined,
				moodle_password: moodlePass || undefined,
				ical_url: icalUrl || undefined
			});
		} catch (err: any) {
			error = err.message || "Erreur lors de la création du compte";
		} finally {
			isSubmitting = false;
		}
	}
</script>

<div class="min-h-screen flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 bg-app-bg text-zinc-100 font-sans">
	<div class="sm:mx-auto sm:w-full sm:max-w-md text-center space-y-3">
		<div class="inline-flex items-center justify-center">
			<img src="/icon.png" alt="Cisco" class="w-16 h-16 rounded-xl object-contain shadow-2xl" />
		</div>
		<h1 class="text-3xl font-extrabold tracking-tight text-white">
			CISCO STUDENT
		</h1>
		<p class="text-sm text-zinc-400">
			Le tableau de bord unifié pour étudiants en <strong>BUT Réseaux & Télécoms</strong>
		</p>
		<div class="flex items-center justify-center gap-2 pt-1">
			<Badge variant="cisco">ScoDoc API</Badge>
			<Badge variant="secondary">Moodle Mobile</Badge>
			<Badge variant="outline">ADE Campus iCal</Badge>
		</div>
	</div>

	<div class="mt-8 sm:mx-auto sm:w-full {mode === 'register' ? 'sm:max-w-2xl' : 'sm:max-w-md'}">
		<Card class="p-6 sm:p-8 border-app-border bg-app-card shadow-2xl rounded-xl">
			<!-- Tab Switcher -->
			<div class="grid grid-cols-2 p-1 bg-app-surface rounded-lg mb-6 border border-app-border">
				<button
					type="button"
					onclick={() => (mode = "login")}
					class="py-2 text-xs font-semibold rounded-md transition-all cursor-pointer {mode === 'login' ? 'bg-white/[0.08] text-white shadow-xs' : 'text-zinc-400 hover:text-zinc-200'}"
				>
					Se Connecter
				</button>
				<button
					type="button"
					onclick={() => (mode = "register")}
					class="py-2 text-xs font-semibold rounded-md transition-all cursor-pointer {mode === 'register' ? 'bg-white/[0.08] text-white shadow-xs' : 'text-zinc-400 hover:text-zinc-200'}"
				>
					Créer un Compte
				</button>
			</div>

			{#if error}
				<div class="p-3 mb-5 rounded-lg bg-red-600/20 text-red-300 text-xs font-medium">
					{error}
				</div>
			{/if}

			{#if mode === "login"}
				<!-- Formulaire Connexion -->
				<form onsubmit={handleLogin} class="space-y-4">
					<div>
						<label for="l-user" class="block text-xs font-medium text-zinc-300 mb-1">Identifiant</label>
						<div class="relative">
							<User class="w-4 h-4 text-zinc-500 absolute left-3 top-2.5" />
							<input
								id="l-user"
								type="text"
								bind:value={loginUsername}
								required
								class="w-full rounded-lg border border-app-border bg-app-surface pl-9 pr-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-cyan-500 focus:outline-none"
								placeholder="ex: prenom.nom"
							/>
						</div>
					</div>

					<div>
						<label for="l-pwd" class="block text-xs font-medium text-zinc-300 mb-1">Mot de passe</label>
						<div class="relative">
							<Lock class="w-4 h-4 text-zinc-500 absolute left-3 top-2.5" />
							<input
								id="l-pwd"
								type="password"
								bind:value={loginPassword}
								required
								class="w-full rounded-lg border border-app-border bg-app-surface pl-9 pr-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-cyan-500 focus:outline-none"
								placeholder="••••••••••••"
							/>
						</div>
					</div>

					<Button variant="cisco" type="submit" class="w-full" disabled={isSubmitting}>
						{isSubmitting ? "Connexion en cours..." : "Accéder à mon Dashboard"}
						<ArrowRight class="w-4 h-4" />
					</Button>
				</form>
			{:else}
				<!-- Formulaire Inscription avec services tiers intégrés -->
				<form onsubmit={handleRegister} class="space-y-4">
					<div class="border-b border-app-border pb-3">
						<h3 class="text-xs font-bold uppercase tracking-wider text-cyan-400 mb-2">1. Compte Dashboard Cisco</h3>
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
							<div>
								<label for="r-name" class="block text-xs font-medium text-zinc-400 mb-1">Nom & Prénom *</label>
								<input
									id="r-name"
									type="text"
									bind:value={regFullName}
									required
									placeholder="ex: Jean Dupont"
									class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-1.5 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none"
								/>
							</div>
							<div>
								<label for="r-user" class="block text-xs font-medium text-zinc-400 mb-1">Identifiant de connexion *</label>
								<input
									id="r-user"
									type="text"
									bind:value={regUsername}
									required
									placeholder="ex: jean.dupont"
									class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-1.5 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none"
								/>
							</div>
							<div>
								<label for="r-email" class="block text-xs font-medium text-zinc-400 mb-1">Email universitaire *</label>
								<input
									id="r-email"
									type="email"
									bind:value={regEmail}
									required
									placeholder="prenom.nom@etu.umontpellier.fr"
									class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-1.5 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none"
								/>
							</div>
							<div>
								<label for="r-pwd" class="block text-xs font-medium text-zinc-400 mb-1">Mot de passe de l'application *</label>
								<input
									id="r-pwd"
									type="password"
									bind:value={regPassword}
									required
									placeholder="••••••••••••"
									class="w-full rounded-lg border border-app-border bg-app-surface px-3 py-1.5 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none"
								/>
							</div>
						</div>
					</div>

					<!-- Section ScoDoc -->
					<div class="border-b border-app-border pb-3">
						<h3 class="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-2">2. Identifiants ScoDoc (Notes & Absences)</h3>
						<div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
							<div>
								<label for="r-sco-url" class="block text-[11px] text-zinc-400 mb-0.5">URL ScoDoc</label>
								<input
									id="r-sco-url"
									type="text"
									bind:value={scodocUrl}
									class="w-full rounded-lg border border-app-border bg-app-surface px-2.5 py-1 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none"
								/>
							</div>
							<div>
								<label for="r-sco-u" class="block text-[11px] text-zinc-400 mb-0.5">Identifiant CAS</label>
								<input
									id="r-sco-u"
									type="text"
									bind:value={scodocUser}
									placeholder="prenom.nom"
									class="w-full rounded-lg border border-app-border bg-app-surface px-2.5 py-1 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none"
								/>
							</div>
							<div>
								<label for="r-sco-p" class="block text-[11px] text-zinc-400 mb-0.5">Mot de passe CAS</label>
								<input
									id="r-sco-p"
									type="password"
									bind:value={scodocPass}
									placeholder="••••••••"
									class="w-full rounded-lg border border-app-border bg-app-surface px-2.5 py-1 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none"
								/>
							</div>
						</div>
					</div>

					<!-- Section Moodle -->
					<div class="border-b border-app-border pb-3">
						<h3 class="text-xs font-bold uppercase tracking-wider text-amber-400 mb-2">3. Accès Moodle (Devoirs & DM)</h3>
						<div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
							<div>
								<label for="r-mdl-url" class="block text-[11px] text-zinc-400 mb-0.5">URL Moodle</label>
								<input
									id="r-mdl-url"
									type="text"
									bind:value={moodleUrl}
									class="w-full rounded-lg border border-app-border bg-app-surface px-2.5 py-1 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none"
								/>
							</div>
							<div>
								<label for="r-mdl-u" class="block text-[11px] text-zinc-400 mb-0.5">Identifiant Moodle</label>
								<input
									id="r-mdl-u"
									type="text"
									bind:value={moodleUser}
									placeholder="ex: jdupont"
									class="w-full rounded-lg border border-app-border bg-app-surface px-2.5 py-1 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none"
								/>
							</div>
							<div>
								<label for="r-mdl-p" class="block text-[11px] text-zinc-400 mb-0.5">Mot de passe Moodle</label>
								<input
									id="r-mdl-p"
									type="password"
									bind:value={moodlePass}
									placeholder="••••••••"
									class="w-full rounded-lg border border-app-border bg-app-surface px-2.5 py-1 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none"
								/>
							</div>
						</div>
					</div>

					<!-- Section ADE iCal -->
					<div>
						<h3 class="text-xs font-bold uppercase tracking-wider text-blue-400 mb-2">4. Emploi du Temps UM Montpellier (ADE Campus)</h3>
						<div>
							<label for="r-ical" class="block text-[11px] text-zinc-400 mb-0.5">Lien iCal exporté (.ics)</label>
							<input
								id="r-ical"
								type="url"
								bind:value={icalUrl}
								placeholder="https://edt.umontpellier.fr/.../export.ics"
								class="w-full rounded-lg border border-app-border bg-app-surface px-2.5 py-1 text-xs text-zinc-100 focus:border-cyan-500 focus:outline-none"
							/>
						</div>
					</div>

					<Button variant="cisco" type="submit" class="w-full mt-4" disabled={isSubmitting}>
						{isSubmitting ? "Création du compte..." : "Créer mon Compte & Accéder au Panel"}
						<ArrowRight class="w-4 h-4" />
					</Button>
				</form>
			{/if}
		</Card>
	</div>
</div>
