<script lang="ts">
	import { onMount } from "svelte";
	import { api } from "$lib/api";
	import { auth } from "$lib/stores/auth.svelte";
	import Card from "../Card.svelte";
	import Skeleton from "../Skeleton.svelte";
	import { ShieldCheck, Server, Users, Trash2, KeyRound, Pencil, Send, Check, X, Search } from "lucide-svelte";

	let isLoading = $state(true);
	let error = $state("");
	let notice = $state("");

	// SMTP
	let smtp = $state<any>(null);
	let smtpPassword = $state("");
	let isSavingSmtp = $state(false);
	let testTarget = $state("");

	// Utilisateurs
	let users = $state<any[]>([]);
	let search = $state("");
	let managed = $state<any>(null); // utilisateur en cours de gestion
	let editName = $state("");
	let editEmail = $state("");
	let newPassword = $state("");
	let isBusy = $state(false);

	let filteredUsers = $derived(
		users.filter((u) => {
			const q = search.trim().toLowerCase();
			return !q || u.email.toLowerCase().includes(q) || (u.full_name || "").toLowerCase().includes(q);
		})
	);

	function flash(message: string) {
		notice = message;
		setTimeout(() => (notice = ""), 3500);
	}

	async function load() {
		try {
			[smtp, users] = await Promise.all([api.adminGetSmtp(), api.adminListUsers()]);
		} catch (e: any) {
			error = e.message || "Chargement impossible.";
		} finally {
			isLoading = false;
		}
	}

	onMount(load);

	async function saveSmtp(e: SubmitEvent) {
		e.preventDefault();
		isSavingSmtp = true;
		error = "";
		try {
			smtp = await api.adminUpdateSmtp({
				host: smtp.host,
				port: Number(smtp.port),
				security: smtp.security,
				username: smtp.username,
				password: smtpPassword ? smtpPassword : null,
				from_email: smtp.from_email,
				from_name: smtp.from_name,
				public_url: smtp.public_url
			});
			smtpPassword = "";
			flash("Configuration SMTP enregistrée.");
		} catch (err: any) {
			error = err.message;
		} finally {
			isSavingSmtp = false;
		}
	}

	async function testSmtp() {
		error = "";
		try {
			const res = await api.adminTestSmtp(testTarget.trim() || undefined);
			flash(res.message);
		} catch (err: any) {
			error = err.message;
		}
	}

	function manage(user: any) {
		managed = user;
		editName = user.full_name || "";
		editEmail = user.email;
		newPassword = "";
	}

	async function saveUser() {
		isBusy = true;
		error = "";
		try {
			const updated = await api.adminUpdateUser(managed.id, { full_name: editName, email: editEmail });
			users = users.map((u) => (u.id === updated.id ? { ...u, ...updated, task_count: u.task_count } : u));
			managed = users.find((u) => u.id === updated.id);
			flash("Utilisateur mis à jour.");
		} catch (err: any) {
			error = err.message;
		} finally {
			isBusy = false;
		}
	}

	async function savePassword() {
		isBusy = true;
		error = "";
		try {
			await api.adminSetPassword(managed.id, newPassword);
			newPassword = "";
			flash("Mot de passe modifié.");
		} catch (err: any) {
			error = err.message;
		} finally {
			isBusy = false;
		}
	}

	async function deleteUser() {
		if (!confirm(`Supprimer définitivement le compte ${managed.email} et toutes ses données ?`)) return;
		isBusy = true;
		error = "";
		try {
			await api.adminDeleteUser(managed.id);
			users = users.filter((u) => u.id !== managed.id);
			managed = null;
			flash("Compte supprimé.");
		} catch (err: any) {
			error = err.message;
		} finally {
			isBusy = false;
		}
	}

	function formatDate(iso: string | null) {
		return iso ? new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" }) : "--";
	}

	const inputClass = "w-full rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs text-fg placeholder:text-subtle focus:border-cyan-500 focus:outline-none";
</script>

<div class="space-y-6">
	<div class="pb-2 border-b border-app-border">
		<h1 class="text-xl font-bold tracking-tight text-fg">Administration</h1>
	</div>

	{#if error}
		<div class="rounded-lg bg-red-600/20 p-3 text-xs text-red-300 font-medium flex justify-between gap-2">
			<span>{error}</span>
			<button onclick={() => (error = "")} aria-label="Fermer" class="cursor-pointer"><X class="w-3.5 h-3.5" /></button>
		</div>
	{/if}
	{#if notice}
		<div class="rounded-lg bg-emerald-600/20 p-3 text-xs text-emerald-300 font-medium flex items-center gap-2">
			<Check class="w-3.5 h-3.5" />{notice}
		</div>
	{/if}

	{#if isLoading}
		<Skeleton class="h-64 w-full" />
		<Skeleton class="h-48 w-full" />
	{:else}
		<!-- SMTP -->
		<Card>
			<div class="flex items-center justify-between gap-3 mb-4">
				<div class="flex items-center gap-2.5">
					<Server class="w-4 h-4 text-cyan-400" />
					<h2 class="text-sm font-semibold text-fg">Serveur SMTP</h2>
				</div>
				<span class="px-2.5 py-0.5 rounded-full text-[10px] font-medium {smtp.configured ? 'bg-emerald-600/15 text-emerald-400' : 'bg-app-raised text-muted'}">
					{smtp.configured ? "Configuré" : "Non configuré"}
				</span>
			</div>
			<form onsubmit={saveSmtp} class="space-y-3">
				<div class="grid grid-cols-1 sm:grid-cols-6 gap-3">
					<div class="sm:col-span-3">
						<label for="smtp-host" class="block text-xs font-medium text-muted mb-1">Serveur</label>
						<input id="smtp-host" bind:value={smtp.host} placeholder="smtp.example.com" class={inputClass} />
					</div>
					<div class="sm:col-span-1">
						<label for="smtp-port" class="block text-xs font-medium text-muted mb-1">Port</label>
						<input id="smtp-port" type="number" min="1" max="65535" bind:value={smtp.port} class={inputClass} />
					</div>
					<div class="sm:col-span-2">
						<label for="smtp-sec" class="block text-xs font-medium text-muted mb-1">Sécurité</label>
						<select id="smtp-sec" bind:value={smtp.security} class={inputClass}>
							<option value="starttls">STARTTLS (587)</option>
							<option value="ssl">SSL/TLS (465)</option>
							<option value="none">Aucune (25)</option>
						</select>
					</div>
					<div class="sm:col-span-3">
						<label for="smtp-user" class="block text-xs font-medium text-muted mb-1">Identifiant</label>
						<input id="smtp-user" bind:value={smtp.username} autocomplete="off" class={inputClass} />
					</div>
					<div class="sm:col-span-3">
						<label for="smtp-pwd" class="block text-xs font-medium text-muted mb-1">Mot de passe</label>
						<input id="smtp-pwd" type="password" bind:value={smtpPassword} autocomplete="new-password" placeholder={smtp.has_password ? "Inchangé (laisser vide)" : ""} class={inputClass} />
					</div>
					<div class="sm:col-span-3">
						<label for="smtp-from" class="block text-xs font-medium text-muted mb-1">Adresse d'expédition</label>
						<input id="smtp-from" type="email" bind:value={smtp.from_email} placeholder="noreply@example.com" class={inputClass} />
					</div>
					<div class="sm:col-span-3">
						<label for="smtp-name" class="block text-xs font-medium text-muted mb-1">Nom d'expéditeur</label>
						<input id="smtp-name" bind:value={smtp.from_name} class={inputClass} />
					</div>
					<div class="sm:col-span-6">
						<label for="smtp-url" class="block text-xs font-medium text-muted mb-1">URL publique du site (liens « mot de passe oublié »)</label>
						<input id="smtp-url" type="url" bind:value={smtp.public_url} placeholder="https://cisco.example.com" class={inputClass} />
					</div>
				</div>
				<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-app-border">
					<div class="flex gap-2">
						<input type="email" bind:value={testTarget} placeholder="Destinataire du test (vous par défaut)" aria-label="Destinataire du test" class={inputClass} />
						<button type="button" onclick={testSmtp} disabled={!smtp.configured} class="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-app-border bg-app-surface hover:bg-fg/[0.04] disabled:opacity-40 text-xs text-muted cursor-pointer shrink-0">
							<Send class="w-3.5 h-3.5" />Tester
						</button>
					</div>
					<button type="submit" disabled={isSavingSmtp} class="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold cursor-pointer">
						{isSavingSmtp ? "Enregistrement..." : "Enregistrer"}
					</button>
				</div>
			</form>
		</Card>

		<!-- Utilisateurs -->
		<Card>
			<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
				<div class="flex items-center gap-2.5">
					<Users class="w-4 h-4 text-cyan-400" />
					<h2 class="text-sm font-semibold text-fg">Utilisateurs <span class="text-subtle font-normal">({users.length})</span></h2>
				</div>
				<div class="relative sm:w-64">
					<Search class="w-3.5 h-3.5 text-subtle absolute left-3 top-2.5" />
					<input bind:value={search} placeholder="Rechercher…" aria-label="Rechercher un utilisateur" class="{inputClass} pl-8" />
				</div>
			</div>

			<div class="divide-y divide-app-border -mx-1">
				{#each filteredUsers as user (user.id)}
					<div class="px-1 py-3">
						<button onclick={() => (managed?.id === user.id ? (managed = null) : manage(user))} class="w-full flex items-center gap-3 text-left cursor-pointer">
							<div class="w-8 h-8 rounded-full bg-app-surface border border-app-border flex items-center justify-center text-xs font-bold text-cyan-400 shrink-0">
								{(user.full_name || user.email).slice(0, 2).toUpperCase()}
							</div>
							<div class="min-w-0 flex-1">
								<div class="text-xs font-bold text-fg truncate">
									{user.full_name || user.email}
									{#if user.is_admin}<span class="ml-1.5 text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-cyan-600/15 text-cyan-400">Admin</span>{/if}
								</div>
								<div class="text-xs text-muted truncate">{user.email} · inscrit le {formatDate(user.created_at)}</div>
							</div>
							<div class="hidden sm:flex items-center gap-1.5 text-[10px] shrink-0">
								<span class="px-2 py-0.5 rounded-full {user.has_scodoc ? 'bg-emerald-600/15 text-emerald-400' : 'bg-app-raised text-subtle'}">ScoDoc</span>
								<span class="px-2 py-0.5 rounded-full {user.has_moodle ? 'bg-emerald-600/15 text-emerald-400' : 'bg-app-raised text-subtle'}">Moodle</span>
								<span class="px-2 py-0.5 rounded-full {user.has_ical ? 'bg-emerald-600/15 text-emerald-400' : 'bg-app-raised text-subtle'}">Emploi du temps</span>
								<span class="text-subtle ml-1">{user.task_count} devoir{user.task_count > 1 ? "s" : ""}</span>
							</div>
						</button>

						{#if managed?.id === user.id}
							<div class="mt-3 ml-0 sm:ml-11 grid grid-cols-1 lg:grid-cols-2 gap-4 border-t border-app-border pt-4">
								<div class="space-y-2">
									<div class="flex items-center gap-1.5 text-xs font-semibold text-muted"><Pencil class="w-3.5 h-3.5" />Profil</div>
									<input bind:value={editName} placeholder="Nom complet" aria-label="Nom complet" class={inputClass} />
									<input type="email" bind:value={editEmail} disabled={user.is_admin} aria-label="Email" class="{inputClass} disabled:opacity-50" />
									<button onclick={saveUser} disabled={isBusy} class="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold cursor-pointer">Enregistrer</button>
								</div>
								<div class="space-y-2">
									<div class="flex items-center gap-1.5 text-xs font-semibold text-muted"><KeyRound class="w-3.5 h-3.5" />Mot de passe</div>
									<input type="password" bind:value={newPassword} minlength="8" autocomplete="new-password" placeholder="Nouveau mot de passe (8 car. min.)" aria-label="Nouveau mot de passe" class={inputClass} />
									<button onclick={savePassword} disabled={isBusy || newPassword.length < 8} class="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white text-xs font-semibold cursor-pointer">Changer le mot de passe</button>
								</div>
								{#if !user.is_admin && user.id !== auth.user?.id}
									<div class="lg:col-span-2 pt-3 border-t border-app-border flex justify-end">
										<button onclick={deleteUser} disabled={isBusy} class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-600/20 hover:bg-red-600/30 text-red-300 text-xs font-semibold cursor-pointer">
											<Trash2 class="w-3.5 h-3.5" />Supprimer ce compte
										</button>
									</div>
								{/if}
							</div>
						{/if}
					</div>
				{:else}
					<div class="py-8 text-center text-xs text-subtle">Aucun utilisateur trouvé.</div>
				{/each}
			</div>
		</Card>
	{/if}
</div>
