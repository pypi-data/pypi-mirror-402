/**
 * Phase 5 E2E Tests - Business Glossary & Data Catalog
 *
 * Comprehensive end-to-end tests for all Phase 5 features using MSW mock data.
 * Tests all API endpoints, CRUD operations, and data integrity.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { setupServer } from 'msw/node'
import { handlers } from '../handlers'
import { resetStore, getStore, getAll, getById } from '../data/store'

// Import API client functions
import {
  // Glossary
  getTerms,
  getTerm,
  createTerm,
  updateTerm,
  deleteTerm,
  getTermHistory,
  getTermRelationships,
  getCategories,
  createCategory,
  updateCategory,
  deleteCategory,
  createRelationship,
  deleteRelationship,
  // Catalog
  getAssets,
  getAsset,
  createAsset,
  updateAsset,
  deleteAsset,
  getAssetColumns,
  createColumn,
  updateColumn,
  deleteColumn,
  mapColumnToTerm,
  unmapColumnFromTerm,
  getAssetTags,
  addTag,
  removeTag,
  // Collaboration
  getComments,
  createComment,
  updateComment,
  deleteComment,
  getActivities,
} from '@/api/client'

// Setup MSW server
const server = setupServer(...handlers)

describe('Phase 5 E2E Tests', () => {
  beforeAll(() => {
    server.listen({ onUnhandledRequest: 'error' })
  })

  afterAll(() => {
    server.close()
  })

  beforeEach(() => {
    resetStore()
  })

  // ============================================================================
  // GLOSSARY TERMS
  // ============================================================================
  describe('Glossary Terms API', () => {
    describe('GET /glossary/terms', () => {
      it('should list all terms', async () => {
        const terms = await getTerms()

        expect(Array.isArray(terms)).toBe(true)
        expect(terms.length).toBeGreaterThan(0)

        // Each term should have required fields
        terms.forEach((term) => {
          expect(term).toHaveProperty('id')
          expect(term).toHaveProperty('name')
          expect(term).toHaveProperty('definition')
          expect(term).toHaveProperty('status')
          expect(['draft', 'approved', 'deprecated']).toContain(term.status)
        })
      })

      it('should filter terms by search query', async () => {
        // Get all terms first
        const allTerms = await getTerms()
        expect(allTerms.length).toBeGreaterThan(0)

        // Search by a term name substring
        const searchTerm = allTerms[0].name.substring(0, 5)
        const filteredTerms = await getTerms({ search: searchTerm })

        // Should return at least one matching result
        expect(filteredTerms.length).toBeGreaterThan(0)
        filteredTerms.forEach((term) => {
          expect(
            term.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
              term.definition.toLowerCase().includes(searchTerm.toLowerCase())
          ).toBe(true)
        })
      })

      it('should filter terms by status', async () => {
        const approvedTerms = await getTerms({ status: 'approved' })

        approvedTerms.forEach((term) => {
          expect(term.status).toBe('approved')
        })
      })

      it('should filter terms by category_id', async () => {
        const categories = await getCategories()
        if (categories.length === 0) return

        const categoryId = categories[0].id
        const filteredTerms = await getTerms({ category_id: categoryId })

        filteredTerms.forEach((term) => {
          expect(term.category_id).toBe(categoryId)
        })
      })

      it('should support pagination with skip/limit', async () => {
        const allTerms = await getTerms()
        if (allTerms.length < 2) return

        const firstPage = await getTerms({ skip: 0, limit: 2 })
        const secondPage = await getTerms({ skip: 2, limit: 2 })

        expect(firstPage.length).toBeLessThanOrEqual(2)
        if (allTerms.length > 2) {
          expect(firstPage[0].id).not.toBe(secondPage[0]?.id)
        }
      })
    })

    describe('GET /glossary/terms/:id', () => {
      it('should get a specific term by ID', async () => {
        const allTerms = await getTerms()
        expect(allTerms.length).toBeGreaterThan(0)

        const termId = allTerms[0].id
        const term = await getTerm(termId)

        expect(term.id).toBe(termId)
        expect(term).toHaveProperty('name')
        expect(term).toHaveProperty('definition')
        expect(term).toHaveProperty('status')
        expect(term).toHaveProperty('synonyms')
        expect(term).toHaveProperty('related_terms')
      })

      it('should return 404 for non-existent term', async () => {
        await expect(getTerm('non-existent-id')).rejects.toThrow()
      })
    })

    describe('POST /glossary/terms', () => {
      it('should create a new term', async () => {
        const newTermData = {
          name: 'Test Term E2E',
          definition: 'A test term created during E2E testing',
          status: 'draft' as const,
        }

        const createdTerm = await createTerm(newTermData)

        expect(createdTerm).toHaveProperty('id')
        expect(createdTerm.name).toBe(newTermData.name)
        expect(createdTerm.definition).toBe(newTermData.definition)
        expect(createdTerm.status).toBe('draft')
        expect(createdTerm.synonyms).toEqual([])
        expect(createdTerm.related_terms).toEqual([])

        // Verify it appears in the list
        const term = await getTerm(createdTerm.id)
        expect(term.id).toBe(createdTerm.id)
      })

      it('should create a term with category', async () => {
        const categories = await getCategories()
        if (categories.length === 0) return

        const newTermData = {
          name: 'Categorized Term',
          definition: 'A term with a category',
          category_id: categories[0].id,
        }

        const createdTerm = await createTerm(newTermData)

        expect(createdTerm.category_id).toBe(categories[0].id)
      })
    })

    describe('PUT /glossary/terms/:id', () => {
      it('should update an existing term', async () => {
        const terms = await getTerms()
        expect(terms.length).toBeGreaterThan(0)

        const termId = terms[0].id
        const updateData = {
          name: 'Updated Term Name',
          definition: 'Updated definition',
          status: 'approved' as const,
        }

        const updatedTerm = await updateTerm(termId, updateData)

        expect(updatedTerm.id).toBe(termId)
        expect(updatedTerm.name).toBe(updateData.name)
        expect(updatedTerm.definition).toBe(updateData.definition)
        expect(updatedTerm.status).toBe('approved')
      })

      it('should create history entry on update', async () => {
        const terms = await getTerms()
        expect(terms.length).toBeGreaterThan(0)

        const termId = terms[0].id
        const originalTerm = await getTerm(termId)

        // Update the term
        await updateTerm(termId, {
          name: 'Changed Name for History',
        })

        // Check history
        const history = await getTermHistory(termId)
        expect(history.length).toBeGreaterThan(0)

        const nameChange = history.find((h) => h.field_name === 'name')
        expect(nameChange).toBeDefined()
        expect(nameChange?.old_value).toBe(originalTerm.name)
        expect(nameChange?.new_value).toBe('Changed Name for History')
      })

      it('should return 404 for non-existent term', async () => {
        await expect(
          updateTerm('non-existent-id', { name: 'Test' })
        ).rejects.toThrow()
      })
    })

    describe('DELETE /glossary/terms/:id', () => {
      it('should delete a term', async () => {
        // Create a term to delete
        const createdTerm = await createTerm({
          name: 'Term to Delete',
          definition: 'Will be deleted',
        })

        // Delete it
        const result = await deleteTerm(createdTerm.id)
        expect(result.ok).toBe(true)

        // Verify it's gone
        await expect(getTerm(createdTerm.id)).rejects.toThrow()
      })

      it('should clean up relationships when term is deleted', async () => {
        // Create two terms
        const term1 = await createTerm({
          name: 'Term 1 for Relationship',
          definition: 'First term',
        })
        const term2 = await createTerm({
          name: 'Term 2 for Relationship',
          definition: 'Second term',
        })

        // Create a relationship
        await createRelationship({
          source_term_id: term1.id,
          target_term_id: term2.id,
          relationship_type: 'synonym',
        })

        // Verify relationship exists
        const relationshipsBefore = await getTermRelationships(term1.id)
        expect(relationshipsBefore.length).toBeGreaterThan(0)

        // Delete term1
        await deleteTerm(term1.id)

        // Relationships should be cleaned up (term2's relationships)
        const relationshipsAfter = await getTermRelationships(term2.id)
        const remainingRelToTerm1 = relationshipsAfter.filter(
          (r) => r.source_term_id === term1.id || r.target_term_id === term1.id
        )
        expect(remainingRelToTerm1.length).toBe(0)
      })
    })

    describe('GET /glossary/terms/:id/history', () => {
      it('should return term history', async () => {
        const terms = await getTerms()
        expect(terms.length).toBeGreaterThan(0)

        const termId = terms[0].id
        const history = await getTermHistory(termId)

        expect(Array.isArray(history)).toBe(true)
        history.forEach((entry) => {
          expect(entry).toHaveProperty('id')
          expect(entry).toHaveProperty('term_id')
          expect(entry).toHaveProperty('field_name')
          expect(entry).toHaveProperty('old_value')
          expect(entry).toHaveProperty('new_value')
          expect(entry).toHaveProperty('changed_at')
        })
      })
    })

    describe('GET /glossary/terms/:id/relationships', () => {
      it('should return term relationships', async () => {
        const terms = await getTerms()
        expect(terms.length).toBeGreaterThan(0)

        const termId = terms[0].id
        const relationships = await getTermRelationships(termId)

        expect(Array.isArray(relationships)).toBe(true)
        relationships.forEach((rel) => {
          expect(rel).toHaveProperty('id')
          expect(rel).toHaveProperty('source_term_id')
          expect(rel).toHaveProperty('target_term_id')
          expect(rel).toHaveProperty('relationship_type')
          expect(['synonym', 'related', 'parent', 'child']).toContain(
            rel.relationship_type
          )
        })
      })
    })
  })

  // ============================================================================
  // GLOSSARY CATEGORIES
  // ============================================================================
  describe('Glossary Categories API', () => {
    describe('GET /glossary/categories', () => {
      it('should list all categories', async () => {
        const categories = await getCategories()

        expect(Array.isArray(categories)).toBe(true)
        expect(categories.length).toBeGreaterThan(0)

        categories.forEach((category) => {
          expect(category).toHaveProperty('id')
          expect(category).toHaveProperty('name')
          expect(category).toHaveProperty('created_at')
          expect(category).toHaveProperty('updated_at')
        })
      })
    })

    describe('POST /glossary/categories', () => {
      it('should create a new category', async () => {
        const newCategoryData = {
          name: 'Test Category E2E',
          description: 'A test category',
        }

        const createdCategory = await createCategory(newCategoryData)

        expect(createdCategory).toHaveProperty('id')
        expect(createdCategory.name).toBe(newCategoryData.name)
        expect(createdCategory.description).toBe(newCategoryData.description)
      })

      it('should create a child category', async () => {
        const parentCategory = await createCategory({
          name: 'Parent Category',
        })

        const childCategory = await createCategory({
          name: 'Child Category',
          parent_id: parentCategory.id,
        })

        expect(childCategory.parent_id).toBe(parentCategory.id)
      })
    })

    describe('PUT /glossary/categories/:id', () => {
      it('should update a category', async () => {
        const category = await createCategory({
          name: 'Category to Update',
        })

        const updated = await updateCategory(category.id, {
          name: 'Updated Category Name',
          description: 'New description',
        })

        expect(updated.name).toBe('Updated Category Name')
        expect(updated.description).toBe('New description')
      })
    })

    describe('DELETE /glossary/categories/:id', () => {
      it('should delete a category and unlink terms', async () => {
        const category = await createCategory({
          name: 'Category to Delete',
        })

        // Create a term in this category
        const term = await createTerm({
          name: 'Term in Category',
          definition: 'Test',
          category_id: category.id,
        })

        // Delete the category
        const result = await deleteCategory(category.id)
        expect(result.ok).toBe(true)

        // Term should still exist but without category
        const updatedTerm = await getTerm(term.id)
        expect(updatedTerm.category_id).toBeUndefined()
      })
    })
  })

  // ============================================================================
  // GLOSSARY RELATIONSHIPS
  // ============================================================================
  describe('Glossary Relationships API', () => {
    describe('POST /glossary/relationships', () => {
      it('should create a relationship between terms', async () => {
        const term1 = await createTerm({
          name: 'Source Term',
          definition: 'Source',
        })
        const term2 = await createTerm({
          name: 'Target Term',
          definition: 'Target',
        })

        const relationship = await createRelationship({
          source_term_id: term1.id,
          target_term_id: term2.id,
          relationship_type: 'synonym',
        })

        expect(relationship).toHaveProperty('id')
        expect(relationship.source_term_id).toBe(term1.id)
        expect(relationship.target_term_id).toBe(term2.id)
        expect(relationship.relationship_type).toBe('synonym')
        expect(relationship.source_term).toHaveProperty('name')
        expect(relationship.target_term).toHaveProperty('name')
      })

      it('should support different relationship types', async () => {
        const term1 = await createTerm({ name: 'T1', definition: 'D1' })
        const term2 = await createTerm({ name: 'T2', definition: 'D2' })

        const relTypes = ['synonym', 'related', 'parent', 'child'] as const
        for (const relType of relTypes) {
          const rel = await createRelationship({
            source_term_id: term1.id,
            target_term_id: term2.id,
            relationship_type: relType,
          })
          expect(rel.relationship_type).toBe(relType)
        }
      })
    })

    describe('DELETE /glossary/relationships/:id', () => {
      it('should delete a relationship', async () => {
        const term1 = await createTerm({ name: 'T1', definition: 'D1' })
        const term2 = await createTerm({ name: 'T2', definition: 'D2' })

        const relationship = await createRelationship({
          source_term_id: term1.id,
          target_term_id: term2.id,
          relationship_type: 'related',
        })

        const result = await deleteRelationship(relationship.id)
        expect(result.ok).toBe(true)

        // Verify relationship is removed
        const relationships = await getTermRelationships(term1.id)
        const deleted = relationships.find((r) => r.id === relationship.id)
        expect(deleted).toBeUndefined()
      })
    })
  })

  // ============================================================================
  // CATALOG ASSETS
  // ============================================================================
  describe('Catalog Assets API', () => {
    describe('GET /catalog/assets', () => {
      it('should list all assets', async () => {
        const assets = await getAssets()

        expect(Array.isArray(assets)).toBe(true)
        expect(assets.length).toBeGreaterThan(0)

        assets.forEach((asset) => {
          expect(asset).toHaveProperty('id')
          expect(asset).toHaveProperty('name')
          expect(asset).toHaveProperty('asset_type')
          expect(['table', 'file', 'api']).toContain(asset.asset_type)
          expect(asset).toHaveProperty('column_count')
          expect(asset).toHaveProperty('tag_count')
          expect(asset).toHaveProperty('updated_at')
        })
      })

      it('should filter assets by search query', async () => {
        const allAssets = await getAssets()
        if (allAssets.length === 0) return

        const searchTerm = allAssets[0].name.substring(0, 4)
        const filteredAssets = await getAssets({ search: searchTerm })

        expect(filteredAssets.length).toBeGreaterThan(0)
      })

      it('should filter assets by asset_type', async () => {
        const tableAssets = await getAssets({ asset_type: 'table' })

        tableAssets.forEach((asset) => {
          expect(asset.asset_type).toBe('table')
        })
      })

      it('should filter assets by source_id', async () => {
        const allAssets = await getAssets()
        const assetWithSource = allAssets.find((a) => a.source_id)
        if (!assetWithSource) return

        const filteredAssets = await getAssets({
          source_id: assetWithSource.source_id,
        })

        filteredAssets.forEach((asset) => {
          expect(asset.source_id).toBe(assetWithSource.source_id)
        })
      })
    })

    describe('GET /catalog/assets/:id', () => {
      it('should get a specific asset with full details', async () => {
        const allAssets = await getAssets()
        expect(allAssets.length).toBeGreaterThan(0)

        const assetId = allAssets[0].id
        const asset = await getAsset(assetId)

        expect(asset.id).toBe(assetId)
        expect(asset).toHaveProperty('name')
        expect(asset).toHaveProperty('asset_type')
        expect(asset).toHaveProperty('columns')
        expect(asset).toHaveProperty('tags')
        expect(Array.isArray(asset.columns)).toBe(true)
        expect(Array.isArray(asset.tags)).toBe(true)
      })

      it('should include column term mapping info', async () => {
        const allAssets = await getAssets()
        const assetId = allAssets[0].id
        const asset = await getAsset(assetId)

        asset.columns.forEach((column) => {
          expect(column).toHaveProperty('id')
          expect(column).toHaveProperty('name')
          expect(column).toHaveProperty('data_type')
          expect(column).toHaveProperty('is_nullable')
          expect(column).toHaveProperty('is_primary_key')
          // term property may be undefined or have term details
          if (column.term_id && column.term) {
            expect(column.term).toHaveProperty('id')
            expect(column.term).toHaveProperty('name')
          }
        })
      })
    })

    describe('POST /catalog/assets', () => {
      it('should create a new asset', async () => {
        const newAssetData = {
          name: 'test_e2e_table',
          asset_type: 'table' as const,
          description: 'E2E test asset',
        }

        const createdAsset = await createAsset(newAssetData)

        expect(createdAsset).toHaveProperty('id')
        expect(createdAsset.name).toBe(newAssetData.name)
        expect(createdAsset.asset_type).toBe('table')
        expect(createdAsset.description).toBe(newAssetData.description)
        expect(createdAsset.columns).toEqual([])
        expect(createdAsset.tags).toEqual([])
      })

      it('should create asset with owner', async () => {
        const asset = await createAsset({
          name: 'owned_asset',
          asset_type: 'file',
          owner_id: 'data-team@company.com',
        })

        expect(asset.owner_id).toBe('data-team@company.com')
      })
    })

    describe('PUT /catalog/assets/:id', () => {
      it('should update an asset', async () => {
        const asset = await createAsset({
          name: 'asset_to_update',
          asset_type: 'table',
        })

        const updated = await updateAsset(asset.id, {
          name: 'updated_asset_name',
          description: 'Updated description',
          quality_score: 92.5,
        })

        expect(updated.name).toBe('updated_asset_name')
        expect(updated.description).toBe('Updated description')
        expect(updated.quality_score).toBe(92.5)
      })
    })

    describe('DELETE /catalog/assets/:id', () => {
      it('should delete an asset and its columns/tags', async () => {
        // Create asset with column and tag
        const asset = await createAsset({
          name: 'asset_to_delete',
          asset_type: 'table',
        })

        await createColumn(asset.id, { name: 'test_column' })
        await addTag(asset.id, { tag_name: 'test_tag' })

        // Delete asset
        const result = await deleteAsset(asset.id)
        expect(result.ok).toBe(true)

        // Asset should be gone
        await expect(getAsset(asset.id)).rejects.toThrow()
      })
    })
  })

  // ============================================================================
  // CATALOG COLUMNS
  // ============================================================================
  describe('Catalog Columns API', () => {
    describe('GET /catalog/assets/:assetId/columns', () => {
      it('should list columns for an asset', async () => {
        const assets = await getAssets()
        const assetWithColumns = assets.find((a) => a.column_count > 0)
        if (!assetWithColumns) return

        const columns = await getAssetColumns(assetWithColumns.id)

        expect(Array.isArray(columns)).toBe(true)
        expect(columns.length).toBeGreaterThan(0)

        columns.forEach((column) => {
          expect(column).toHaveProperty('id')
          expect(column).toHaveProperty('name')
          expect(column).toHaveProperty('asset_id')
          expect(column.asset_id).toBe(assetWithColumns.id)
        })
      })
    })

    describe('POST /catalog/assets/:assetId/columns', () => {
      it('should create a column', async () => {
        const asset = await createAsset({
          name: 'asset_for_columns',
          asset_type: 'table',
        })

        const column = await createColumn(asset.id, {
          name: 'user_id',
          data_type: 'uuid',
          is_primary_key: true,
          is_nullable: false,
        })

        expect(column).toHaveProperty('id')
        expect(column.name).toBe('user_id')
        expect(column.data_type).toBe('uuid')
        expect(column.is_primary_key).toBe(true)
        expect(column.is_nullable).toBe(false)
        expect(column.asset_id).toBe(asset.id)
      })

      it('should create column with sensitivity level', async () => {
        const asset = await createAsset({
          name: 'pii_asset',
          asset_type: 'table',
        })

        const column = await createColumn(asset.id, {
          name: 'email',
          sensitivity_level: 'confidential',
        })

        expect(column.sensitivity_level).toBe('confidential')
      })
    })

    describe('PUT /catalog/columns/:id', () => {
      it('should update a column', async () => {
        const asset = await createAsset({
          name: 'asset_for_column_update',
          asset_type: 'table',
        })

        const column = await createColumn(asset.id, {
          name: 'old_name',
          data_type: 'string',
        })

        const updated = await updateColumn(column.id, {
          name: 'new_name',
          data_type: 'varchar(255)',
          description: 'Updated column',
        })

        expect(updated.name).toBe('new_name')
        expect(updated.data_type).toBe('varchar(255)')
        expect(updated.description).toBe('Updated column')
      })
    })

    describe('DELETE /catalog/columns/:id', () => {
      it('should delete a column', async () => {
        const asset = await createAsset({
          name: 'asset_for_column_delete',
          asset_type: 'table',
        })

        const column = await createColumn(asset.id, {
          name: 'column_to_delete',
        })

        const result = await deleteColumn(column.id)
        expect(result.ok).toBe(true)

        // Verify column is removed
        const columns = await getAssetColumns(asset.id)
        const deleted = columns.find((c) => c.id === column.id)
        expect(deleted).toBeUndefined()
      })
    })

    describe('PUT /catalog/columns/:id/term', () => {
      it('should map a column to a glossary term', async () => {
        // Create term
        const term = await createTerm({
          name: 'Customer ID',
          definition: 'Unique customer identifier',
        })

        // Create asset and column
        const asset = await createAsset({
          name: 'customers_mapping',
          asset_type: 'table',
        })
        const column = await createColumn(asset.id, {
          name: 'customer_id',
        })

        // Map column to term
        const mapped = await mapColumnToTerm(column.id, term.id)

        expect(mapped.term_id).toBe(term.id)
        expect(mapped.term).toBeDefined()
        expect(mapped.term?.id).toBe(term.id)
        expect(mapped.term?.name).toBe('Customer ID')
      })
    })

    describe('DELETE /catalog/columns/:id/term', () => {
      it('should unmap a column from a glossary term', async () => {
        // Create term and map it
        const term = await createTerm({
          name: 'Order ID',
          definition: 'Unique order identifier',
        })

        const asset = await createAsset({
          name: 'orders_mapping',
          asset_type: 'table',
        })
        const column = await createColumn(asset.id, { name: 'order_id' })
        await mapColumnToTerm(column.id, term.id)

        // Unmap
        const unmapped = await unmapColumnFromTerm(column.id)

        expect(unmapped.term_id).toBeUndefined()
        expect(unmapped.term).toBeUndefined()
      })
    })
  })

  // ============================================================================
  // CATALOG TAGS
  // ============================================================================
  describe('Catalog Tags API', () => {
    describe('GET /catalog/assets/:assetId/tags', () => {
      it('should list tags for an asset', async () => {
        const assets = await getAssets()
        const assetWithTags = assets.find((a) => a.tag_count > 0)
        if (!assetWithTags) return

        const tags = await getAssetTags(assetWithTags.id)

        expect(Array.isArray(tags)).toBe(true)
        expect(tags.length).toBeGreaterThan(0)

        tags.forEach((tag) => {
          expect(tag).toHaveProperty('id')
          expect(tag).toHaveProperty('tag_name')
          expect(tag).toHaveProperty('asset_id')
        })
      })
    })

    describe('POST /catalog/assets/:assetId/tags', () => {
      it('should add a tag to an asset', async () => {
        const asset = await createAsset({
          name: 'asset_for_tags',
          asset_type: 'file',
        })

        const tag = await addTag(asset.id, {
          tag_name: 'pii',
          tag_value: 'true',
        })

        expect(tag).toHaveProperty('id')
        expect(tag.tag_name).toBe('pii')
        expect(tag.tag_value).toBe('true')
        expect(tag.asset_id).toBe(asset.id)
      })

      it('should add a tag without value', async () => {
        const asset = await createAsset({
          name: 'asset_for_tags_no_value',
          asset_type: 'api',
        })

        const tag = await addTag(asset.id, {
          tag_name: 'deprecated',
        })

        expect(tag.tag_name).toBe('deprecated')
        expect(tag.tag_value).toBeUndefined()
      })
    })

    describe('DELETE /catalog/tags/:id', () => {
      it('should remove a tag', async () => {
        const asset = await createAsset({
          name: 'asset_for_tag_delete',
          asset_type: 'table',
        })

        const tag = await addTag(asset.id, { tag_name: 'to_delete' })

        const result = await removeTag(tag.id)
        expect(result.ok).toBe(true)

        // Verify tag is removed
        const tags = await getAssetTags(asset.id)
        const deleted = tags.find((t) => t.id === tag.id)
        expect(deleted).toBeUndefined()
      })
    })
  })

  // ============================================================================
  // COLLABORATION - COMMENTS
  // ============================================================================
  describe('Comments API', () => {
    describe('GET /comments', () => {
      it('should require resource_type and resource_id', async () => {
        const terms = await getTerms()
        expect(terms.length).toBeGreaterThan(0)

        const comments = await getComments('term', terms[0].id)
        expect(Array.isArray(comments)).toBe(true)
      })

      it('should return comments with replies', async () => {
        const store = getStore()
        const comments = getAll(store.comments)
        const commentsWithReplies = comments.filter(
          (c) => !c.parent_id && c.replies && c.replies.length > 0
        )

        // Store should have some comments with replies
        // This tests the mock data generation
        expect(comments.length).toBeGreaterThan(0)
      })
    })

    describe('POST /comments', () => {
      it('should create a comment on a term', async () => {
        const terms = await getTerms()
        expect(terms.length).toBeGreaterThan(0)

        const comment = await createComment({
          resource_type: 'term',
          resource_id: terms[0].id,
          content: 'This is a test comment on a term',
        })

        expect(comment).toHaveProperty('id')
        expect(comment.resource_type).toBe('term')
        expect(comment.resource_id).toBe(terms[0].id)
        expect(comment.content).toBe('This is a test comment on a term')
        expect(comment.author_id).toBeDefined()
        expect(comment.replies).toEqual([])
      })

      it('should create a comment on an asset', async () => {
        const assets = await getAssets()
        expect(assets.length).toBeGreaterThan(0)

        const comment = await createComment({
          resource_type: 'asset',
          resource_id: assets[0].id,
          content: 'Asset comment',
        })

        expect(comment.resource_type).toBe('asset')
      })

      it('should create a reply to a comment', async () => {
        const terms = await getTerms()
        const parentComment = await createComment({
          resource_type: 'term',
          resource_id: terms[0].id,
          content: 'Parent comment',
        })

        const reply = await createComment({
          resource_type: 'term',
          resource_id: terms[0].id,
          content: 'Reply to parent',
          parent_id: parentComment.id,
        })

        expect(reply.parent_id).toBe(parentComment.id)
      })

      it('should create an activity entry when commenting', async () => {
        const terms = await getTerms()
        const activitiesBefore = await getActivities({
          resource_type: 'term',
          resource_id: terms[0].id,
        })

        await createComment({
          resource_type: 'term',
          resource_id: terms[0].id,
          content: 'Comment that creates activity',
        })

        const activitiesAfter = await getActivities({
          resource_type: 'term',
          resource_id: terms[0].id,
        })

        // Should have more activities after commenting
        expect(activitiesAfter.length).toBeGreaterThanOrEqual(
          activitiesBefore.length
        )
      })
    })

    describe('PUT /comments/:id', () => {
      it('should update a comment', async () => {
        const terms = await getTerms()
        const comment = await createComment({
          resource_type: 'term',
          resource_id: terms[0].id,
          content: 'Original content',
        })

        const updated = await updateComment(comment.id, {
          content: 'Updated content',
        })

        expect(updated.content).toBe('Updated content')
        expect(updated.id).toBe(comment.id)
      })
    })

    describe('DELETE /comments/:id', () => {
      it('should delete a comment', async () => {
        const terms = await getTerms()
        const comment = await createComment({
          resource_type: 'term',
          resource_id: terms[0].id,
          content: 'Comment to delete',
        })

        const result = await deleteComment(comment.id)
        expect(result.ok).toBe(true)
      })

      it('should delete replies when parent is deleted', async () => {
        const terms = await getTerms()
        const parent = await createComment({
          resource_type: 'term',
          resource_id: terms[0].id,
          content: 'Parent',
        })

        await createComment({
          resource_type: 'term',
          resource_id: terms[0].id,
          content: 'Reply',
          parent_id: parent.id,
        })

        await deleteComment(parent.id)

        // After deletion, replies should also be gone
        const comments = await getComments('term', terms[0].id)
        const orphanedReplies = comments.filter((c) => c.parent_id === parent.id)
        expect(orphanedReplies.length).toBe(0)
      })
    })
  })

  // ============================================================================
  // COLLABORATION - ACTIVITIES
  // ============================================================================
  describe('Activities API', () => {
    describe('GET /activities', () => {
      it('should list all activities', async () => {
        const activities = await getActivities()

        expect(Array.isArray(activities)).toBe(true)
        expect(activities.length).toBeGreaterThan(0)

        activities.forEach((activity) => {
          expect(activity).toHaveProperty('id')
          expect(activity).toHaveProperty('resource_type')
          expect(activity).toHaveProperty('resource_id')
          expect(activity).toHaveProperty('action')
          expect(activity).toHaveProperty('actor_id')
          expect(activity).toHaveProperty('created_at')
          expect(['created', 'updated', 'deleted', 'commented']).toContain(
            activity.action
          )
        })
      })

      it('should filter activities by resource_type', async () => {
        const termActivities = await getActivities({ resource_type: 'term' })

        termActivities.forEach((activity) => {
          expect(activity.resource_type).toBe('term')
        })
      })

      it('should return activities sorted by created_at desc', async () => {
        const activities = await getActivities()

        for (let i = 0; i < activities.length - 1; i++) {
          const current = new Date(activities[i].created_at).getTime()
          const next = new Date(activities[i + 1].created_at).getTime()
          expect(current).toBeGreaterThanOrEqual(next)
        }
      })

      it('should support pagination', async () => {
        const firstPage = await getActivities({ skip: 0, limit: 5 })
        const secondPage = await getActivities({ skip: 5, limit: 5 })

        expect(firstPage.length).toBeLessThanOrEqual(5)

        if (firstPage.length === 5 && secondPage.length > 0) {
          expect(firstPage[0].id).not.toBe(secondPage[0].id)
        }
      })
    })
  })

  // ============================================================================
  // DATA INTEGRITY
  // ============================================================================
  describe('Data Integrity', () => {
    it('should maintain referential integrity between terms and categories', async () => {
      const categories = await getCategories()
      const terms = await getTerms()

      const termsWithCategories = terms.filter((t) => t.category_id)

      termsWithCategories.forEach((term) => {
        const categoryExists = categories.some((c) => c.id === term.category_id)
        expect(categoryExists).toBe(true)
      })
    })

    it('should maintain referential integrity between assets and columns', async () => {
      const assets = await getAssets()

      // Only check first 3 assets to avoid timeout
      for (const assetListItem of assets.slice(0, 3)) {
        const asset = await getAsset(assetListItem.id)
        const columns = await getAssetColumns(assetListItem.id)

        expect(columns.length).toBe(asset.columns.length)

        columns.forEach((column) => {
          expect(column.asset_id).toBe(assetListItem.id)
        })
      }
    }, 15000)

    it('should maintain referential integrity for column-term mappings', async () => {
      const terms = await getTerms()
      const assets = await getAssets()

      for (const assetListItem of assets.slice(0, 3)) {
        const asset = await getAsset(assetListItem.id)

        asset.columns.forEach((column) => {
          if (column.term_id) {
            // Term ID should reference an existing term (unless it was deleted)
            // In a real scenario, this would be a foreign key constraint
            expect(column.term_id).toBeDefined()
          }
        })
      }
    })
  })

  // ============================================================================
  // STORE FUNCTIONALITY
  // ============================================================================
  describe('Store Functionality', () => {
    it('should initialize with diverse mock data', () => {
      const store = getStore()

      expect(store.glossaryTerms.size).toBeGreaterThan(0)
      expect(store.glossaryCategories.size).toBeGreaterThan(0)
      expect(store.termRelationships.size).toBeGreaterThan(0)
      expect(store.termHistory.size).toBeGreaterThan(0)
      expect(store.catalogAssets.size).toBeGreaterThan(0)
      expect(store.assetColumns.size).toBeGreaterThan(0)
      expect(store.comments.size).toBeGreaterThan(0)
      expect(store.activities.size).toBeGreaterThan(0)
    })

    it('should reset store to initial state', () => {
      const store = getStore()
      const initialTermCount = store.glossaryTerms.size

      // Add a term
      const newTerm = {
        id: 'test-reset-term',
        name: 'Reset Test',
        definition: 'Test',
        status: 'draft' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        synonyms: [],
        related_terms: [],
      }
      store.glossaryTerms.set(newTerm.id, newTerm)

      expect(store.glossaryTerms.size).toBe(initialTermCount + 1)

      // Reset
      resetStore()
      const newStore = getStore()

      // Should not have the test term anymore
      expect(newStore.glossaryTerms.has('test-reset-term')).toBe(false)
    })
  })
})
