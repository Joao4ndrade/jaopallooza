export interface EventInfo {
  name: string
  tagline: string | null
  description: string | null
  starts_at: string | null
  ends_at: string | null
  venue_name: string | null
  venue_address: string | null
  city: string | null
  maps_url: string | null
  tickets_count: number
  invite_required: boolean
}

export interface Person {
  id: string
  name: string
}

export interface CategoryRef {
  id: number
  title: string
  emoji: string
}

export interface Me {
  id: string
  name: string
  is_admin: boolean
  has_ticket: boolean
  awards_opt_in: boolean
  created_at: string
  partner: Person | null
  partner_status: 'none' | 'pending' | 'confirmed'
  partner_requests: Person[]
  competing_in: CategoryRef[]
}

export interface Ticket {
  code: string
  holder_name: string
  created_at: string
  checked_in_at: string | null
}

export interface Nominee {
  id: string
  name: string
  members: string[]
}

export interface AwardCategory {
  id: number
  slug: string
  title: string
  description: string | null
  emoji: string
  kind: 'individual' | 'couple'
  nominees: Nominee[]
  my_vote: { nominee: Nominee; voted_at: string } | null
  i_am_nominee: boolean
}

export interface AwardsData {
  can_vote: boolean
  categories: AwardCategory[]
}
