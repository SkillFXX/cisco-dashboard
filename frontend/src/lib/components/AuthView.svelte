<script lang="ts">
	import { auth } from "$lib/stores/auth.svelte";
	import Card from "./Card.svelte";
	import Button from "./Button.svelte";
	import Badge from "./Badge.svelte";
	import { ArrowRight, Mail, Lock } from "lucide-svelte";

	let mode = $state<"login" | "register">("login");

	// Login state
	let loginEmail = $state("");
	let loginPassword = $state("");

	// Register state
	let regEmail = $state("");
	let regPassword = $state("");

	let isSubmitting = $state(false);
	let error = $state("");

	async function handleLogin(e: SubmitEvent) {
		e.preventDefault();
		isSubmitting = true;
		error = "";
		try {
			await auth.login(loginEmail, loginPassword);
		} catch (err: any) {
			error = err.message || "Adresse email ou mot de passe incorrect";
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
				email: regEmail,
				password: regPassword
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

	<div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
		<Card class="p-6 sm:p-8 border-app-border bg-app-card shadow-2xl rounded-xl">
			<!-- Tab Switcher -->
			<div class="grid grid-cols-2 p-1 bg-app-surface rounded-lg mb-6 border border-app-border">
				<button
					type="button"
					onclick={() => { mode = "login"; error = ""; }}
					class="py-2 text-xs font-semibold rounded-md transition-all cursor-pointer {mode === 'login' ? 'bg-white/[0.08] text-white shadow-xs' : 'text-zinc-400 hover:text-zinc-200'}"
				>
					Se Connecter
				</button>
				<button
					type="button"
					onclick={() => { mode = "register"; error = ""; }}
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
						<label for="l-email" class="block text-xs font-medium text-zinc-300 mb-1">Adresse email</label>
						<div class="relative">
							<Mail class="w-4 h-4 text-zinc-500 absolute left-3 top-2.5" />
							<input
								id="l-email"
								type="email"
								bind:value={loginEmail}
								required
								class="w-full rounded-lg border border-app-border bg-app-surface pl-9 pr-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-cyan-500 focus:outline-none"
								placeholder="votre.email@etu.umontpellier.fr"
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
				<!-- Formulaire Inscription minimaliste (Email + Mot de passe uniquement) -->
				<form onsubmit={handleRegister} class="space-y-4">
					<div>
						<label for="r-email" class="block text-xs font-medium text-zinc-300 mb-1">Adresse email</label>
						<div class="relative">
							<Mail class="w-4 h-4 text-zinc-500 absolute left-3 top-2.5" />
							<input
								id="r-email"
								type="email"
								bind:value={regEmail}
								required
								class="w-full rounded-lg border border-app-border bg-app-surface pl-9 pr-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-cyan-500 focus:outline-none"
								placeholder="votre.email@etu.umontpellier.fr"
							/>
						</div>
					</div>

					<div>
						<label for="r-pwd" class="block text-xs font-medium text-zinc-300 mb-1">Mot de passe</label>
						<div class="relative">
							<Lock class="w-4 h-4 text-zinc-500 absolute left-3 top-2.5" />
							<input
								id="r-pwd"
								type="password"
								bind:value={regPassword}
								required
								minlength="4"
								class="w-full rounded-lg border border-app-border bg-app-surface pl-9 pr-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-cyan-500 focus:outline-none"
								placeholder="••••••••••••"
							/>
						</div>
					</div>

					<p class="text-[11px] text-zinc-400 leading-relaxed pt-1">
						Votre nom, prénom et accès aux services (ScoDoc, Moodle, ADE) pourront être configurés ou modifiés à tout moment dans les Paramètres.
					</p>

					<Button variant="cisco" type="submit" class="w-full mt-2" disabled={isSubmitting}>
						{isSubmitting ? "Création en cours..." : "Créer mon Compte"}
						<ArrowRight class="w-4 h-4" />
					</Button>
				</form>
			{/if}
		</Card>
	</div>
</div>
