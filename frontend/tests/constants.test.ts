import { describe, it, expect } from 'vitest'
import { INITIAL_AVAILABILITY } from '../src/constants/availability'
import { CATEGORY_LABELS_FR } from '../src/constants/categories'
import { MEALS, MEAL_LABELS_FR } from '../src/constants/meals'
import { WEEK_DAYS, WEEK_DAY_LABELS_FR } from '../src/constants/weekdays'

describe('Constants', () => {
  describe('Availability', () => {
    it('should have all weekdays set to available by default', () => {
      WEEK_DAYS.forEach(day => {
        expect(INITIAL_AVAILABILITY[day].lunch).toBe(true)
        expect(INITIAL_AVAILABILITY[day].dinner).toBe(true)
      })
    })

    it('should have availability for all 7 days', () => {
      expect(Object.keys(INITIAL_AVAILABILITY)).toHaveLength(7)
    })
  })

  describe('Categories', () => {
    it('should have French labels for all categories', () => {
      expect(CATEGORY_LABELS_FR.lunch).toBe('Déjeuner')
      expect(CATEGORY_LABELS_FR.dinner).toBe('Dîner')
      expect(CATEGORY_LABELS_FR.weekends_lunch).toBe('Weekend déjeuner')
      expect(CATEGORY_LABELS_FR.saturday_dinner).toBe('Samedi dîner')
    })

    it('should have 4 category types', () => {
      expect(Object.keys(CATEGORY_LABELS_FR)).toHaveLength(4)
    })
  })

  describe('Meals', () => {
    it('should have lunch and dinner', () => {
      expect(MEALS).toContain('lunch')
      expect(MEALS).toContain('dinner')
      expect(MEALS).toHaveLength(2)
    })

    it('should have French labels for meals', () => {
      expect(MEAL_LABELS_FR.lunch).toBe('Déjeuner')
      expect(MEAL_LABELS_FR.dinner).toBe('Dîner')
    })
  })

  describe('Weekdays', () => {
    it('should have all 7 days starting from Monday', () => {
      expect(WEEK_DAYS).toHaveLength(7)
      expect(WEEK_DAYS[0]).toBe('monday')
      expect(WEEK_DAYS[6]).toBe('sunday')
    })

    it('should have French labels for all weekdays', () => {
      expect(WEEK_DAY_LABELS_FR.monday).toBe('Lundi')
      expect(WEEK_DAY_LABELS_FR.tuesday).toBe('Mardi')
      expect(WEEK_DAY_LABELS_FR.wednesday).toBe('Mercredi')
      expect(WEEK_DAY_LABELS_FR.thursday).toBe('Jeudi')
      expect(WEEK_DAY_LABELS_FR.friday).toBe('Vendredi')
      expect(WEEK_DAY_LABELS_FR.saturday).toBe('Samedi')
      expect(WEEK_DAY_LABELS_FR.sunday).toBe('Dimanche')
    })
  })
})
